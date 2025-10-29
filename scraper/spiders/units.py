import json
import re
import traceback
from collections import defaultdict
from typing import Any, Generator

from parsel import Selector, SelectorList
from pydantic import BaseModel
from scrapy.http import Response
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from typing_extensions import Literal

from api.models import (
    Course,
    CourseHourEnum,
    CourseLecturerLink,
    Department,
    LearningUnit,
    Level,
    NamedURL,
    OccurenceEnum,
    Periodicity,
    Section,
    SemesterCourses,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
    UnitType,
    UnitTypeLegends,
)
from api.util.types import CourseSlot, CourseTypeEnum, WeekdayEnum
from scraper.env import Settings
from scraper.util.logging import KeywordLoggerSpider
from scraper.util.mappings import UnitDepartmentMapping, UnitLevelMapping
from scraper.util.regex_rules import (
    RE_ABSCHNITTID,
    RE_CODE,
    RE_DATE,
    RE_DOZIDE,
    RE_SEMKEZ,
    RE_UNITID,
)
from scraper.util.scrapercache import CACHE_PATH
from scraper.util.table import Table, table_under_header
from scraper.util.url import edit_url_key


def get_urls(year: int, semester: Literal["W", "S"]):
    # seite=0 shows all results in one page
    url = f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?semkez={year}{semester}&ansicht=2&seite=0"

    # gets all sections and courses in english/german
    yield url + "&lang=en"
    yield url + "&lang=de"

    # find all courses that are part of each department
    for dept in list(Department):
        yield url + f"&deptId={dept.value}&lang=en"
    # find all courses that are part of each level
    for level in list(Level):
        yield url + f"&studiengangTyp={level.value}&lang=en"


class UnitsSpider(KeywordLoggerSpider):
    """
    The main learning unit (lerneinheit) scraper that handles scraping all the lecture-specific data that is available on VVZ.

    1.  Initially we scrape the root page with all the catalogue data (ansicht=2). We scrape in both English and German.
        url: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?semkez=2025W&ansicht=2&seite=0
    2.  We can read all the course data from that page. But we also need the additional information like literature,
        assessment, groups, etc. for each lecture. These are the same for both German/English, so we only scrape specific
        course pages in English.
    3.  The root page also lists all the programmes and their sections, so we can create a hierarchy of sections and what
        course is part of which section.
    4.  The departments (CS, math, etc.) and levels (BSC, MSC, etc.) are not visible on the root page. To figure out what
        course is part of which dept/level, we also scrape the root page filtered by each department/level and then simply
        keep track of what courses we see.
    5.  Courses are some type inside a programme. For example, "Chemie I" in 2025W is "O" (or "Obligatorisch") in the
        "Agricultural Sciences Bachelor" programme. These legends can be different for each programme and semester, so we
        additionally scrape these.
    """

    name = "units"
    start_urls = [
        url
        for year in range(Settings().start_year, Settings().end_year + 1)
        for semester in Settings().read_semesters()
        for url in get_urls(year, semester)
    ]
    rules = (
        Rule(
            LinkExtractor(
                # Only view the english version of a full lecture details page
                allow=r"lerneinheit\.view",
                deny=r"lang=de",
                canonicalize=True,
                process_value=lambda url: edit_url_key(url, "ansicht", ["ALLE"]),
            ),
            follow=True,
            callback="parse_unit",
        ),
        Rule(
            LinkExtractor(
                allow=r"legendeStudienplanangaben\.view",
                deny=r"lang=de",
                canonicalize=True,
            ),
            follow=True,
            callback="parse_legend",
        ),
    )

    def parse(self, response: Response):
        try:
            catalog_semkez = re.search(RE_SEMKEZ, response.url)
            if not catalog_semkez:
                self.logger.error(
                    "No semkez found",
                    extra={
                        "url": response.url,
                        "request_url": response.request.url
                        if response.request
                        else None,
                    },
                )
                return
            catalog_semkez = catalog_semkez.group(1)

            level = re.search(r"studiengangTyp=(\w+)", response.url)
            if level:
                level = Level(level.group(1))
            dept = re.search(r"deptId=(\d+)", response.url)
            if dept:
                dept = Department(int(dept.group(1)))

            # get all the course data
            tables = self.get_unit_tables(response)
            self.logger.info(
                "Found unit tables",
                extra={
                    "count": len(tables),
                    "semkez": catalog_semkez,
                    "dept": dept,
                    "level": level,
                    "url": response.url,
                },
            )

            for id, rows in tables.items():
                unit = self.extract_unit_catalogue_data(id, rows, response.url)
                if not unit:
                    continue
                yield unit

                if level:
                    yield UnitLevelMapping(unit_id=id, level=level)
                if dept:
                    yield UnitDepartmentMapping(unit_id=id, department=dept)

            # get the full section structure
            sec_count = 0
            for section in self.extract_sections(response):
                yield section
                sec_count += 1

            self.logger.info(
                "Parsed all sections",
                extra={"count": sec_count, "semkez": catalog_semkez},
            )

            course_ids = response.css("a::attr(href)")
            course_ids = set(
                [
                    int(cid.re_first(RE_UNITID) or "-1")
                    for cid in course_ids
                    if cid.re_first(RE_UNITID) and catalog_semkez in cid.get()
                ]
            )
            if "lang=en" in response.url:
                yield SemesterCourses(
                    semkez=catalog_semkez,
                    courses=course_ids,
                )

        except Exception as e:
            self.logger.error(
                "Error parsing catalogue page",
                extra={
                    "error": str(e),
                    "url": response.url,
                    "request_url": response.request.url if response.request else None,
                    "traceback": traceback.format_exc(),
                },
            )

    def get_unit_tables(self, response: Response) -> dict[int, SelectorList[Selector]]:
        tables: dict[int, SelectorList[Selector]] = {}

        current_keys: list[Selector] = []
        current_unit_id: int | None = None
        for row in response.xpath("//table[@style='wAuto']//tr"):
            # its the first line of a course
            if unit_id := row.re_first(RE_UNITID):
                if current_unit_id is not None:
                    tables[current_unit_id] = SelectorList(current_keys)
                current_unit_id = int(unit_id)
                current_keys = []
            if current_unit_id is not None:
                current_keys.append(row)

        if current_unit_id is not None:
            tables[current_unit_id] = SelectorList(current_keys)

        return tables

    def extract_unit_catalogue_data(
        self, id: int, rows: SelectorList[Selector], url: str
    ) -> LearningUnit | None:
        """
        Extracts the catalogue data of a course that is available on the main catalogue page.
        The idea is that the returned unit is then passed along to the specific unit page parser,
        which then adds any additional data only available on the unit page, before then yielding
        the final LearningUnit object.

        This function is called for both the German and English versions of the catalogue page for
        each course. In the item pipeline the data is then merged into a single table.
        """

        try:
            semkez = re.search(RE_SEMKEZ, url)
            if not semkez:
                self.logger.error("No semkez found", extra={"url": url})
                return
            semkez = semkez.group(1)
            number = rows[0].re_first(RE_CODE)
            if not number:
                # If there's no number, that usually just means the row is not actually a "unit" row,
                # but just some row that has a link to some other course. For example the following URL
                # has a link to other courses in the "Notice" field which is picked up by our regex:
                # https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=en&semkez=2025W&ansicht=ALLE&lerneinheitId=192500&
                self.logger.debug(
                    "No course number found for unit. Skipping...",
                    extra={"unit_id": id},
                )
                return
            number = number.replace("\xa0", "").strip()
            title = rows[0].css("::text")[1].get()
            title = title.strip() if title else None
            lang = "en" if "lang=en" in url else "de"

            table = Table(rows, pre_parsed=True)
            literature = "\n".join(table.get_texts("literature")) or None
            objective = "\n".join(table.get_texts("learning_objective")) or None
            content = "\n".join(table.get_texts("content")) or None
            lecture_notes = "".join(table.get_texts("lecture_notes")) or None
            additional = "\n".join(table.get_texts("notice")) or None
            comment = "".join(table.get_texts("comment")) or None
            abstract = "".join(table.get_texts("abstract")) or None
            competencies = {}
            if comp_cols := table.find("competencies"):
                competencies = self.extract_competencies(comp_cols)

            if lang == "de":
                return LearningUnit(
                    id=id,
                    number=number,
                    semkez=semkez,
                    title=title,
                    literature=literature,
                    objective=objective,
                    content=content,
                    lecture_notes=lecture_notes,
                    additional=additional,
                    comment=comment,
                    abstract=abstract,
                    competencies=competencies,
                )

            else:
                return LearningUnit(
                    id=id,
                    number=number,
                    semkez=semkez,
                    title_english=title,
                    literature_english=literature,
                    objective_english=objective,
                    content_english=content,
                    lecture_notes_english=lecture_notes,
                    additional_english=additional,
                    comment_english=comment,
                    abstract_english=abstract,
                    competencies_english=competencies,
                )

        except Exception as e:
            self.logger.error(
                "Error extracting unit catalogue data",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "url": url,
                    "id": id,
                },
            )

    def parse_unit(
        self, response: Response
    ) -> Generator[
        UnitExaminerLink
        | UnitLecturerLink
        | LearningUnit
        | Course
        | CourseLecturerLink
        | UnitSectionLink,
        Any,
        None,
    ]:
        """
        Extracts information from a unit page that is not available on the main catalogue page.

        Example url: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en
        """
        try:
            if "red9.ethz.ch" in response.url:
                self.logger.info(
                    "Skipping red9 error page",
                    extra={
                        "url": response.url,
                        "request_url": response.request.url
                        if response.request
                        else None,
                    },
                )
                return
            elif "cookietest=true" in response.url:
                self.logger.info(
                    "Skipping cookietest page",
                    extra={
                        "url": response.url,
                        "request_url": response.request.url
                        if response.request
                        else None,
                    },
                )
                return

            unit_id = re.search(RE_UNITID, response.url)
            if not unit_id:
                self.logger.error(
                    "No unit id found in url", extra={"url": response.url}
                )
                return
            unit_id = int(unit_id.group(1))

            semkez = re.search(RE_SEMKEZ, response.url)
            if not semkez:
                self.logger.error("No semkez found", extra={"url": response.url})
                return
            semkez = semkez.group(1)

            lang = "en" if "lang=en" in response.url else "de"
            if lang == "de":
                raise ValueError(
                    f"Unit page should always be in English. url={response.url}"
                )

            table = Table(response)

            credit_cols = table.find_all("credits")
            credits = None
            two_semester_credits = None
            if len(credit_cols) > 0:
                # two semester credits is shown before the actual course credits
                credits = credit_cols[-1][1].css("::text").get()
                if credits is not None:
                    credits = float(credits.split("\xa0")[0])
            if len(credit_cols) == 2:
                two_semester_credits = credit_cols[0][1].css("::text").get()
                if two_semester_credits is not None:
                    two_semester_credits = float(two_semester_credits.split("\xa0")[0])

            max_places = table.find("places")
            if max_places is not None:
                max_places = max_places[1].css("::text").get()
                if max_places is not None:
                    try:
                        max_places = int(max_places.split(" ")[0])
                    except ValueError:
                        # Cases where we have: "Limited number of places. Special selection procedure."
                        # Example: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=195346&semkez=2025W&ansicht=ALLE&lang=en
                        max_places = -1
            waitlist_end = table.re_first("waiting_list", RE_DATE)
            signup_end = table.re_first("registration_end", RE_DATE)
            signup_start = table.re_first("registration_start", RE_DATE)
            priority = "".join(table.get_texts("priority")) or None
            language = "".join(table.get_texts("language")) or None
            regulations = table.get_texts("regulations")
            written_aids = "".join(table.get_texts("written_aids")) or None
            additional_info = "".join(table.get_texts("additional_info")) or None
            exam_mode = "".join(table.get_texts("exam_mode")) or None
            exam_language = "".join(table.get_texts("exam_language")) or None
            exam_type = "".join(table.get_texts("type")) or None
            course_frequency = table.find("periodicity")
            if course_frequency is not None:
                periodicity_text = course_frequency[1].css("::text").get()
                if periodicity_text in [
                    "jährlich wiederkehrende Veranstaltung",
                    "yearly recurring course",
                ]:
                    course_frequency = Periodicity.ANNUAL
                elif periodicity_text in [
                    "jedes Semester wiederkehrende Veranstaltung",
                    "every semester recurring course",
                ]:
                    course_frequency = Periodicity.SEMESTER
                elif periodicity_text in [
                    "2-jährlich wiederkehrende Veranstaltung",
                    "two-yearly recurring course",
                ]:
                    course_frequency = Periodicity.BIENNIAL
                else:
                    course_frequency = Periodicity.ONETIME
            repetition = "".join(table.get_texts("repetition")) or None
            primary_target_group = table.get_texts("primary_target_group")
            digital = "".join(table.get_texts("digital")) or None
            distance_exam = "".join(table.get_texts("distance_exam")) or None
            exam_block_for = table.get_texts("exam_block")
            occurence = table.find("course")
            general_restrictions = (
                "".join(table.get_texts("general_restrictions")) or None
            )

            if occurence and len(occurence) >= 2:
                occ_text = occurence[1].css("::text").get()
                if occ_text in [
                    "Does not take place this semester.",
                    "Findet dieses Semester nicht statt.",
                ]:
                    occurence = OccurenceEnum.NO
                else:
                    with open(CACHE_PATH / "unknown_occurences.jsonl", "a") as f:
                        f.write(
                            f"{json.dumps({'occurence': occ_text, 'url': response.url})}\n"
                        )
                    occurence = None
            else:
                occurence = None

            groups = self.extract_groups(response)
            offered_in = self.extract_offered_in(response, unit_id)
            for offered in offered_in:
                yield offered

            learning_materials = self.extract_learning_materials(response) or None

            # handle lecturer links
            examiners = table.re("examiners", RE_DOZIDE)
            examiners = [int(pid) for pid in examiners]
            for id in examiners:
                yield UnitExaminerLink(unit_id=unit_id, lecturer_id=id)
            lecturers = table.re("lecturers", RE_DOZIDE)
            lecturers = [int(pid) for pid in lecturers]
            for id in lecturers:
                yield UnitLecturerLink(unit_id=unit_id, lecturer_id=id)

            # TODO: take note of all keys that were not processed

            yield LearningUnit(
                id=unit_id,
                semkez=semkez,
                credits=credits,
                two_semester_credits=two_semester_credits,
                max_places=max_places,
                waitlist_end=waitlist_end,
                signup_end=signup_end,
                signup_start=signup_start,
                priority=priority,
                language=language,
                regulations=regulations,
                written_aids=written_aids,
                additional_info=additional_info,
                exam_mode=exam_mode,
                exam_language=exam_language,
                exam_type=exam_type,
                course_frequency=course_frequency,
                repetition=repetition,
                primary_target_group=primary_target_group,
                digital=digital,
                distance_exam=distance_exam,
                groups=groups,
                exam_block=exam_block_for,
                occurence=occurence,
                general_restrictions=general_restrictions,
                learning_materials=learning_materials,
            )

            # Get courses after the learning unit, to ensure the foreign key exists already
            for k, cols in table.rows:
                course_number = re.match(RE_CODE, k)
                if course_number:
                    for course_or_lecturer in self.extract_course_info(
                        parent_unit=unit_id,
                        semkez=semkez,
                        cols=cols,
                        url=response.url,
                    ):
                        yield course_or_lecturer
        except Exception as e:
            self.logger.error(
                "Error parsing learning unit",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "url": response.url,
                },
            )

    def parse_legend(self, response: Response) -> Generator[UnitTypeLegends, Any, None]:
        """
        Example: www.vvz.ethz.ch/Vorlesungsverzeichnis/legendeStudienplanangaben.view?abschnittId=117361&semkez=2025W&lang=en
        """
        try:
            semkez = re.search(RE_SEMKEZ, response.url)
            id = re.search(RE_ABSCHNITTID, response.url)
            if not semkez or not id:
                self.logger.error(
                    "No semkez or id found",
                    extra={
                        "url": response.url,
                        "request_url": response.request.url
                        if response.request
                        else None,
                    },
                )
                return
            semkez = semkez.group(1)
            id = int(id.group(1))
            title = response.css("h1::text").get()
            if not title:
                self.logger.error(
                    "No title found for legend", extra={"url": response.url}
                )
                return

            table = Table(response.xpath("//table"))
            unit_legends: list[UnitType] = []
            for _, cols in table.rows:
                type = cols[0].css("::text").get()
                description = cols[1].css("::text").get()
                if type and description:
                    unit_legends.append(UnitType(type=type, description=description))
            yield UnitTypeLegends(
                id=id,
                title=title,
                semkez=semkez,
                legend=unit_legends,
            )
        except Exception as e:
            self.logger.error(
                "Error parsing legend",
                extra={
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "url": response.url,
                    "request_url": response.request.url if response.request else None,
                },
            )

    def extract_sections(self, response: Response):
        """
        Extracts all sections visible on the page.
        We keep track of the parent for each section based on the level indicator
        images (small right-facing triangles). We don't care about adding courses to
        their sections here. That is done in the course-parsing function. On the course
        page itself only the top-most (named "Programme") and the bottom-most
        (named "Section") are listed. We only link courses to their
        immediate/bottom-most section. By then keeping track of the parents, we
        can create a recursive SQL query that is able to find all recursive
        children of any (higher-level) section.
        """

        semkez = re.search(RE_SEMKEZ, response.url)
        if not semkez:
            self.logger.error(
                "No semkez found",
                extra={
                    "url": response.url,
                    "request_url": response.request.url if response.request else None,
                },
            )
            return
        semkez = semkez.group(1)

        table = Table(response.xpath("//table"))
        parent_level: list[tuple[int, int]] = []
        for key, cols in table.rows:
            if re.match(RE_CODE, key) or key.startswith("»"):
                continue
            id = cols.re_first(RE_ABSCHNITTID)
            if not id:
                continue
            id = int(id)
            level = len(cols.re('class="levelIndicator"'))
            parent_level.append((level, id))
            name = cols.css("a::text").get()
            comment = "\n".join(cols.css(".kommentar-abschnitt::text").getall()) or None

            # find parentF
            for plevel, pid in reversed(parent_level):
                if plevel < level:
                    parent_id = pid
                    break
            else:
                parent_id = None

            yield Section(
                id=id,
                level=level,
                parent_id=parent_id,
                semkez=semkez,
                name=name if "lang=de" in response.url else None,
                name_english=name if "lang=en" in response.url else None,
                comment=comment if "lang=de" in response.url else None,
                comment_english=comment if "lang=en" in response.url else None,
            )

    def extract_course_info(
        self, parent_unit: int, semkez: str, cols: SelectorList[Selector], url: str
    ) -> Generator[Course | CourseLecturerLink, None, None]:
        if len(cols) == 5:
            number_sel, title_sel, hours_sel, slots_sel, lecturers_sel = cols
        else:
            number_sel, title_sel, hours_sel, lecturers_sel = cols
            slots_sel = None

        number = number_sel.re_first(RE_CODE)
        course_type = None
        if number:
            number = number.replace("\xa0", "")
            try:
                course_type = CourseTypeEnum[number[-1]]
            except KeyError:
                course_type = None
        else:
            self.logger.error(
                "No course code found for unit",
                extra={"url": url, "parent_unit": parent_unit},
            )
            return

        title = title_sel.css("::text").get()
        title = title.strip() if title else None
        comments = "\n".join(
            [
                t.strip()
                for t in title_sel.css(".kommentar-lv::text").getall()
                if t.strip()
            ]
        )
        lecturer_ids = [int(x) for x in lecturers_sel.re(RE_DOZIDE)]

        for id in lecturer_ids:
            yield CourseLecturerLink(
                course_number=number, course_semkez=semkez, lecturer_id=id
            )

        hours_text = hours_sel.css("::text").get()
        hours: float | None = None
        hours_type = None
        if hours_text:
            hours_str = hours_text.split("\xa0")[0]
            if "s" in hours_str:
                hours_type = CourseHourEnum.SEMESTER_HOURS
                hours = float(hours_str.replace("s", ""))
            else:
                hours_type = CourseHourEnum.WEEKLY_HOURS
                hours = float(hours_str)

        """
        Gets the course time slots
        
        Iterates over slot value like: ['Thu', '08:00-09:45', 'UNI', '12:15-13:45', 'UNI']
        To then extract two slots on thursday at different times.

        Or ['Di', '14:15-16:00', 'HG', 'E 7', '»', 'Mi', '09:15-10:00', 'HG', 'E 5', '»']
        To extract a tuesday and wednesday slot.

        USZ rooms have additional room and floor details:
        ['Tue', '17:00-18:00', 'USZ', 'C PAT 22', '»']
        """
        timeslots: list[CourseSlot] = []
        i = 0

        day_info = DayInfo(
            weekday=WeekdayEnum.Invalid,
            date=None,
            first_half_semester=False,
            second_half_semester=False,
            biweekly=False,
        )
        if slots_sel is not None:
            slots = [
                x.replace("\xa0", " ").strip()
                for x in slots_sel.css("::text").getall()
                if x.strip()
            ]
            while i < len(slots):
                try:
                    day_info = get_day_info(slots[i])
                    i += 1
                    if day_info.weekday == WeekdayEnum.ByAppointment and i >= len(
                        slots
                    ):
                        break
                except ValueError:
                    pass

                if "-" in slots[i]:
                    start_time, end_time = slots[i].split("-")
                else:
                    start_time, end_time = None, None

                if len(slots) > i + 1:
                    building = slots[i + 1]
                else:
                    building = None
                if "»" not in slots:
                    # Courses at UNI do not have floor/room info nor a "»" button for more info
                    floor, room = None, None
                    i += 2
                elif len(slots) > i + 2 and " " in slots[i + 2]:
                    floor, room = slots[i + 2].split(" ", 1)
                    i += 4
                else:
                    floor, room = None, None
                    i += 3

                timeslots.append(
                    CourseSlot(
                        weekday=day_info.weekday,
                        date=day_info.date,
                        start_time=start_time,
                        end_time=end_time,
                        building=building,
                        floor=floor,
                        room=room,
                        first_half_semester=day_info.first_half_semester,
                        second_half_semester=day_info.second_half_semester,
                        biweekly=day_info.biweekly,
                    )
                )

        yield Course(
            unit_id=parent_unit,
            number=number,
            title=title,
            semkez=semkez,
            type=course_type,
            comment=comments or None,
            hours=hours,
            hour_type=hours_type,
            timeslots=timeslots,
        )

    def extract_competencies(
        self, cols: SelectorList[Selector]
    ) -> dict[str, dict[str, str]]:
        if len(cols) < 2:
            return {}
        table = Table(cols[1])
        competencies: dict[str, dict[str, str]] = defaultdict(dict)
        prev_key = ""
        for _, r in table.rows:
            columns = r.css("::text").getall()
            if len(columns) == 3:
                prev_key = columns[0].strip()
                competencies[prev_key][columns[1].strip()] = columns[2].strip()
            elif len(columns) == 2:
                competencies[prev_key][columns[0].strip()] = columns[1].strip()
        return competencies

    def extract_groups(self, response: Response) -> dict[str, CourseSlot | None]:
        groups: dict[str, CourseSlot | None] = {}
        table = table_under_header(response, ["Gruppen", "Groups"])
        for _, r in table.rows:
            cols = r.css("::text").getall()
            if len(cols) > 0 and (
                cols[0].startswith("Gruppe") or cols[0].startswith("Groups")
            ):
                cols = cols[1:]

            # Handles cases where theres no information given for groups
            # https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lang=de&lerneinheitId=193540&semkez=2025W&ansicht=ALLE&
            if len(cols) == 1:
                groups[cols[0]] = None
                continue

            if len(cols) != 8:
                self.logger.error(
                    "Unexpected number of columns in groups table",
                    extra={"count": len(cols), "url": response.url, "cols": cols},
                )
                continue
            group, day, time, building, _, floor_room = cols[:6]
            floor, room = floor_room.split(" ")

            day_info = get_day_info(day)

            groups[group] = CourseSlot(
                weekday=day_info.weekday,
                date=day_info.date,
                start_time=time.split("-")[0],
                end_time=time.split("-")[1],
                building=building,
                floor=floor,
                room=room,
                first_half_semester=day_info.first_half_semester,
                second_half_semester=day_info.second_half_semester,
                biweekly=day_info.biweekly,
            )
        return groups

    def extract_learning_materials(
        self, response: Response
    ) -> dict[str, list[NamedURL]]:
        materials: dict[str, list[NamedURL]] = defaultdict(list)
        table = table_under_header(response, ["Lernmaterialien", "Learning materials"])
        prev_key = ""
        for _, r in table.rows:
            if len(r) < 2:
                continue
            key = r[0].css("::text").get()
            if key:
                prev_key = key
            else:
                key = prev_key
            url = r.css("a::attr(href)").get()
            urlname = r.css("a::text").get()
            if key and url and urlname:
                materials[key].append(NamedURL(name=urlname, url=url))
        return materials

    def extract_offered_in(
        self, response: Response, parent_unit_id: int
    ) -> list[UnitSectionLink]:
        offered_in: list[UnitSectionLink] = []
        table = table_under_header(response, ["Angeboten in", "Offered in"])
        for _, r in table.rows:
            id = r[1].re_first(RE_ABSCHNITTID)
            if not id:
                continue
            type = r[2].css("a::text").get()
            type_id = r[2].re_first(RE_ABSCHNITTID)
            if type_id is not None:
                type_id = int(type_id)
            offered_in.append(
                UnitSectionLink(
                    section_id=int(id),
                    unit_id=parent_unit_id,
                    type=type,
                    type_id=type_id,
                )
            )
        return offered_in


class DayInfo(BaseModel):
    weekday: WeekdayEnum
    date: str | None
    first_half_semester: bool
    second_half_semester: bool
    biweekly: bool


def get_day_info(day_str: str) -> DayInfo:
    date = re.match(r"(\d{2})\.(\d{2}).", day_str)
    if date:
        date = day_str.rstrip(".")
        return DayInfo(
            weekday=WeekdayEnum.Date,
            date=date,
            first_half_semester=False,
            second_half_semester=False,
            biweekly=False,
        )
    day, *args = day_str.split("/")
    try:
        # weekday is not always given for every time slot
        weekday = WeekdayEnum.ByAppointment if day == "by appt." else WeekdayEnum[day]
    except KeyError:
        raise ValueError(f"Unknown weekday {day}")

    return DayInfo(
        weekday=weekday,
        date=None,
        first_half_semester="1" in args,
        second_half_semester="2" in args,
        biweekly="2w" in args,
    )
