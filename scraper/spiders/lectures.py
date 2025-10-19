import traceback
from collections import defaultdict
import json
import re
from typing_extensions import Literal
from urllib.parse import urljoin
from parsel import SelectorList, Selector
from pydantic import BaseModel
import scrapy
from scrapy.http import Response

# from api.models import Lecturer
from api.util.types import CourseSlot, CourseTypeEnum, WeekdayEnum
from api.models.course import CourseHourEnum, Course
from api.models.learning_unit import (
    LearningUnit,
    NamedURL,
    OccurenceEnum,
    Periodicity,
    Section,
    UnitSectionLink,
    UnitTypeEnum,
)
from scraper.env import Settings
from scraper.util.keymap import get_key
from scraper.util.regex_rules import (
    RE_ABSCHNITTID,
    RE_CODE,
    RE_DATE,
    RE_DOZIDE,
    RE_LANG,
    RE_UNITID,
    RE_SEMKEZ,
)
from scraper.util.table import Table, table_under_header
from scraper.util.url import (
    delete_url_key,
    edit_url_key,
    sort_url_params,
)


def get_urls(year: int, semester: Literal["W", "S"]):
    # seite=0 shows all results in one page
    url = f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?semkez={year}{semester}&ansicht=1&seite=0"
    return [url + "&lang=en", url + "&lang=de"]


class LecturesSpider(scrapy.Spider):
    name = "lectures"
    start_urls = [
        url
        for year in range(Settings().start_year, Settings().end_year + 1)
        for semester in Settings().read_semesters()
        for url in get_urls(year, semester)
    ]

    def parse(self, response: Response):
        for section in self.extract_sections(response):
            yield section

        for course in response.css("a::attr(href)").getall():
            if "lerneinheit.view" in course:
                url = urljoin(response.url, course)
                url = edit_url_key(url, "ansicht", ["ALLE"])
                url = delete_url_key(url, "lang")
                url = sort_url_params(url)
                yield response.follow(url + "&lang=en", self.parse_unit)
                yield response.follow(url + "&lang=de", self.parse_unit)

    def parse_unit(self, response: Response):
        try:
            unit_title = response.css(
                "section#contentContainer div#contentTop h1::text"
            ).extract_first()
            if not unit_title:
                self.logger.error(f"No course title found for {response.url}")
                return
            unit_title = unit_title.split("\n")
            unit_number = unit_title[0].replace("\xa0", "").strip()
            unit_name = " ".join(unit_title[1:]).strip()

            semkez = re.search(RE_SEMKEZ, response.url)
            if not semkez:
                self.logger.error(f"No semkez found for {response.url}")
                return
            semkez = semkez.group(1)

            unit_id = re.search(RE_UNITID, response.url)
            if not unit_id:
                self.logger.warning(f"No lerneinheitId found for {response.url}")
                unit_id = "unknown"
            else:
                unit_id = unit_id.group(1)
            unit_id = int(unit_id)

            lang = re.search(RE_LANG, response.url)
            if not lang:
                lang = "en"
            else:
                lang = lang.group(1)

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

            literature = "\n".join(table.get_texts("literature")) or None
            objective = "\n".join(table.get_texts("learning_objective")) or None
            content = "\n".join(table.get_texts("content")) or None
            lecture_notes = "".join(table.get_texts("lecture_notes")) or None
            additional = "\n".join(table.get_texts("notice")) or None
            comment = "".join(table.get_texts("comment")) or None

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
            abstract = "".join(table.get_texts("abstract")) or None
            competencies = {}
            if comp_cols := table.find("competencies"):
                competencies = self.extract_competencies(comp_cols)
            examiners = table.re("examiners", RE_DOZIDE)
            examiners = [int(pid) for pid in examiners]
            lecturers = table.re("lecturers", RE_DOZIDE)
            lecturers = [int(pid) for pid in lecturers]
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

            if occurence is not None:
                occ_text = occurence[1].css("::text").get()
                if occ_text in [
                    "Does not take place this semester.",
                    "Findet dieses Semester nicht statt.",
                ]:
                    occurence = OccurenceEnum.NO
                else:
                    with open(
                        ".scrapy/database_cache/unknown_occurences.jsonl", "a"
                    ) as f:
                        f.write(
                            f"{json.dumps({'occurence': occ_text, 'url': response.url})}\n"
                        )
                    occurence = None

            groups = self.extract_groups(response)
            offered_in = self.extract_offered_in(response, unit_id)
            for offered in offered_in:
                yield offered

            learning_materials = self.extract_learning_materials(response)

            # Print any unknown or missed keys
            if lang == "de":
                for k in table.keys():
                    if (
                        k.strip() == ""
                        or re.match(RE_CODE, k)
                        or "zusätzlichen Belegungseinschränkungen" in k
                        or "Information zur Leistungskontrolle" in k
                        or "Leistungskontrolle als Jahreskurs" in k
                        or "Falls die Lerneinheit innerhalb" in k
                        or "Es werden nur die öffentlichen Lernmaterialien aufgeführt"
                        in k
                        or "Keine Informationen zu Gruppen vorhanden" in k
                        or "Semester" in k
                        or "Leistungskontrolle als Semesterkurs" in k
                        or "Keine öffentlichen Lernmaterialien verfügbar." in k
                        or "Gruppe" in k
                        or k == "unkeyed"
                        or k in table.accessed_keys
                        or k in learning_materials.keys()
                    ):
                        continue
                    if get_key(k) == "other":
                        with open(
                            ".scrapy/database_cache/unknown_keys.jsonl", "a"
                        ) as f:
                            f.write(f"{json.dumps({'key': k, 'url': response.url})}\n")

            yield LearningUnit(
                id=unit_id,
                code=unit_number,
                title=unit_name if lang == "de" else None,
                title_english=unit_name if lang == "en" else None,
                semkez=semkez,
                credits=credits,
                two_semester_credits=two_semester_credits,
                literature=literature if lang == "de" else None,
                literature_english=literature if lang == "en" else None,
                objective=objective if lang == "de" else None,
                objective_english=objective if lang == "en" else None,
                content=content if lang == "de" else None,
                content_english=content if lang == "en" else None,
                lecture_notes=lecture_notes if lang == "de" else None,
                lecture_notes_english=lecture_notes if lang == "en" else None,
                additional=additional if lang == "de" else None,
                additional_english=additional if lang == "en" else None,
                comment=comment if lang == "de" else None,
                comment_english=comment if lang == "en" else None,
                max_places=max_places,
                waitlist_end=waitlist_end,
                signup_end=signup_end,
                signup_start=signup_start,
                priority=priority,
                language=language,
                abstract=abstract if lang == "de" else None,
                abstract_english=abstract if lang == "en" else None,
                competencies=competencies if lang == "de" else None,
                competencies_english=competencies if lang == "en" else None,
                regulations=regulations,
                written_aids=written_aids,
                additional_info=additional_info,
                exam_mode=exam_mode,
                exam_language=exam_language,
                exam_type=exam_type,
                examiners=examiners,
                lecturers=lecturers,
                course_frequency=course_frequency,
                repetition=repetition,
                primary_target_group=primary_target_group,
                digital=digital,
                distance_exam=distance_exam,
                groups=groups,
                exam_block=exam_block_for,
                learning_materials=learning_materials if lang == "de" else None,
                learning_materials_english=learning_materials if lang == "en" else None,
                occurence=occurence,
                general_restrictions=general_restrictions,
            )

            # Get courses after the learning unit, to ensure the foreign key exists already
            for k, cols in table.rows:
                course_number = re.match(RE_CODE, k)
                if course_number:
                    yield self.extract_course(
                        parent_unit=unit_id, semkez=semkez, cols=cols
                    )
        except Exception as e:
            self.logger.error(f"Error parsing lerneinheit {response.url}: {e}")
            with open(".scrapy/database_cache/error_pages.jsonl", "a") as f:
                f.write(
                    f"{json.dumps({'error': str(e), 'traceback': traceback.format_exc(), 'url': response.url})}\n"
                )

    def extract_sections(self, response: Response):
        semkez = re.search(RE_SEMKEZ, response.url)
        if not semkez:
            self.logger.error(f"No semkez found for {response.url}")
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

    def extract_course(
        self, parent_unit: int, semkez: str, cols: SelectorList[Selector]
    ) -> Course:
        if len(cols) == 5:
            number_sel, title_sel, hours_sel, slots_sel, lecturers_sel = cols
        else:
            number_sel, title_sel, hours_sel, lecturers_sel = cols
            slots_sel = None

        code = number_sel.re_first(RE_CODE)
        course_type = None
        if code:
            code = code.replace("\xa0", "")
            course_type = CourseTypeEnum[code[-1]]
        title = title_sel.css("::text").get()
        comments = "\n".join(
            [
                t.strip()
                for t in title_sel.css(".kommentar-lv::text").getall()
                if t.strip()
            ]
        )
        lecturer_ids = [int(x) for x in lecturers_sel.re(RE_DOZIDE)]
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
            slots = slots_sel.css("a::text").getall()

            while i < len(slots):
                try:
                    day_info = get_day_info(slots[i])
                    i += 1
                except ValueError:
                    pass

                start_time, end_time = slots[i].split("-")
                building = slots[i + 1]
                if "»" not in slots:
                    # Courses at UNI do not have floor/room info nor a "»" button for more info
                    floor, room = None, None
                    i += 2
                elif len(slots) > i + 2 and " " in slots[i + 2]:
                    floor, room = slots[i + 2].split(" ")
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

        return Course(
            unit_id=parent_unit,
            code=code,
            title=title,
            semkez=semkez,
            type=course_type,
            comment=comments or None,
            hours=hours,
            hour_type=hours_type,
            timeslots=timeslots,
            lecturers=lecturer_ids,
        )

    def extract_competencies(self, cols: SelectorList) -> dict[str, dict[str, str]]:
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
            match type:
                case "O":
                    type = UnitTypeEnum.O
                case "W+":
                    type = UnitTypeEnum.WPlus
                case "W":
                    type = UnitTypeEnum.W
                case "E-":
                    type = UnitTypeEnum.EMinus
                case "Z":
                    type = UnitTypeEnum.Z
                case "Dr":
                    type = UnitTypeEnum.Dr
                case _:
                    type = None
            offered_in.append(
                UnitSectionLink(section_id=int(id), unit_id=parent_unit_id, type=type)
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
