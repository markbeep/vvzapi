import traceback
from collections import defaultdict
import json
import re
from urllib.parse import urljoin
from parsel import SelectorList, Selector
from pydantic import BaseModel
import scrapy
from scrapy.http import Response

# from api.models import Lecturer
from api.models import CourseSlot, CourseTypeEnum, WeekdayEnum
from api.new_models.lehrveranstaltungen import CourseHourEnum, Lehrveranstaltung
from api.new_models.lerneinheit import Lerneinheit, NamedURL, OccurenceEnum, Periodicity
from api.new_models.lehrveranstalter import Lehrveranstalter
from api.new_models.section import Section
from scraper.util.keymap import get_key
from scraper.util.progress import create_progress
from scraper.util.regex_rules import (
    RE_ABSCHNITTID,
    RE_COURSE_NUMBER,
    RE_DATE,
    RE_DOZIDE,
    RE_LANG,
    RE_LERNEINHEITID,
    RE_SEMKEZ,
)
from scraper.util.table import Table, table_under_header
from scraper.util.url import (
    delete_url_key,
    edit_url_key,
    list_url_params,
    sort_url_params,
)


class LecturesSpider(scrapy.Spider):
    name = "lectures"
    start_urls = [
        "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lerneinheitscode=&deptId=&famname=&unterbereichAbschnittId=&lerneinheitstitel=&rufname=&kpRange=0,999&lehrsprache=&bereichAbschnittId=&semkez=2025W&studiengangAbschnittId=&studiengangTyp=&ansicht=1&lang=en&katalogdaten=&wahlinfo=",
        "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lerneinheitscode=&deptId=&famname=&unterbereichAbschnittId=&lerneinheitstitel=&rufname=&kpRange=0,999&lehrsprache=&bereichAbschnittId=&semkez=2025W&studiengangAbschnittId=&studiengangTyp=&ansicht=1&lang=en&katalogdaten=&wahlinfo=&strukturAus=on",
    ]

    def parse(self, response: Response):
        # get current next page
        page_info = response.css(
            ".tabNavi > ul:nth-child(1) > li:nth-child(1)::text"
        ).getall()
        # FORMAT: ['\n', '\xa0Page\xa0 \n  1\xa0 \n  of\xa0 \n  358\n\n  ', '\n\n    ', ' \n  \n\n  ']
        page_info = [x.strip() for x in page_info[1].replace("\xa0", "").split("\n")]
        # FORMAT: ['Page', '1', 'of', '358', '', '']
        current_page = int(page_info[1])
        max_page = int(page_info[3])
        self.logger.info(f"Scraping next page {current_page}")
        self.logger.info(create_progress(current_page, max_page, 80))

        if current_page < max_page:
            search_page_url = edit_url_key(
                response.url, "seite", [str(current_page + 1)]
            )
            # Sort to prevent urls to be viewed as different due to param order
            search_page_url = sort_url_params(search_page_url)
            yield response.follow(search_page_url, self.parse)

        for course in response.css("a::attr(href)").getall():
            if "lerneinheit.view" in course:
                url = urljoin(response.url, course)
                url = edit_url_key(url, "ansicht", ["ALLE"])
                url = delete_url_key(url, "lang")
                url = sort_url_params(url)
                yield response.follow(url + "&lang=en", self.parse_lerneinheit)
                yield response.follow(url + "&lang=de", self.parse_lerneinheit)

    def parse_lerneinheit(self, response: Response):
        try:
            # lecturers might be listed here under examiners, but not under courses.
            # By checking all lecturers on the course page (instead of search page),
            # we ensure that we get all of them.
            for course in response.css("a::attr(href)").getall():
                if "dozent.view" in course:
                    for param in list_url_params(course).keys():
                        if param != "dozide" and param != "semkez":
                            course = delete_url_key(course, param)
                    yield response.follow(course, self.parse_lecturer)

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

            lerneinheitId = re.search(RE_LERNEINHEITID, response.url)
            if not lerneinheitId:
                self.logger.warning(f"No lerneinheitId found for {response.url}")
                lerneinheitId = "unknown"
            else:
                lerneinheitId = lerneinheitId.group(1)
            lerneinheitId = int(lerneinheitId)

            lang = re.search(RE_LANG, response.url)
            if not lang:
                lang = "en"
            else:
                lang = lang.group(1)

            table = Table(response)

            kreditpunkte = table.find_last("credits")
            if kreditpunkte is not None:
                kreditpunkte = kreditpunkte[1].css("::text").get()
                if kreditpunkte is not None:
                    kreditpunkte = float(kreditpunkte.split("\xa0")[0])
            literatur = "\n".join(table.get_texts("literature")) or None
            lernziele = "\n".join(table.get_texts("learning_objective")) or None
            inhalt = "\n".join(table.get_texts("content")) or None
            skript = "".join(table.get_texts("lecture_notes")) or None
            besonderes = "\n".join(table.get_texts("notice")) or None
            # TODO: find german/english name for diplomasupplement
            diplomasupplement = None  # "\n".join(table.get_texts("other")) or None
            angezeigterkommentar = "".join(table.get_texts("comment")) or None
            # TODO: find german/english name for sternkollonne
            sternkollonne = None

            belegungMaxPlatzzahl = table.find("places")
            if belegungMaxPlatzzahl is not None:
                belegungMaxPlatzzahl = belegungMaxPlatzzahl[1].css("::text").get()
                if belegungMaxPlatzzahl is not None:
                    try:
                        belegungMaxPlatzzahl = int(belegungMaxPlatzzahl.split(" ")[0])
                    except ValueError:
                        # Cases where we have: "Limited number of places. Special selection procedure."
                        # Example: https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?lerneinheitId=195346&semkez=2025W&ansicht=ALLE&lang=en
                        belegungMaxPlatzzahl = -1
            belegungTermin2Wl = table.re_first("waiting_list", RE_DATE)
            belegungTermin3Ende = table.re_first("registration_end", RE_DATE)
            belegungsTerminStart = table.re_first("registration_start", RE_DATE)
            vorrang = "".join(table.get_texts("priority")) or None
            lehrsprache = "".join(table.get_texts("language")) or None
            kurzbeschreibung = "".join(table.get_texts("abstract")) or None
            kompetenzen = {}
            if comp_cols := table.find("competencies"):
                kompetenzen = self.extract_competencies(comp_cols)
            prufende = table.re("examiners", RE_DOZIDE)
            prufende = [int(pid) for pid in prufende]
            dozierende = table.re("lecturers", RE_DOZIDE)
            dozierende = [int(pid) for pid in dozierende]
            reglement = table.get_texts("regulations")
            hilfsmittel = "".join(table.get_texts("written_aids")) or None
            prufungzusatzinfo = "".join(table.get_texts("additional_info")) or None
            prufungsmodus = "".join(table.get_texts("exam_mode")) or None
            prufungssprache = "".join(table.get_texts("assessment_language")) or None
            prufungsform = "".join(table.get_texts("type")) or None
            periodicity = table.find("periodicity")
            if periodicity is not None:
                periodicity_text = periodicity[1].css("::text").get()
                if periodicity_text in [
                    "jährlich wiederkehrende Veranstaltung",
                    "yearly recurring course",
                ]:
                    periodicity = Periodicity.ANNUAL
                elif periodicity_text in [
                    "jedes Semester wiederkehrende Veranstaltung",
                    "every semester recurring course",
                ]:
                    periodicity = Periodicity.SEMESTER
                else:
                    periodicity = Periodicity.ONETIME
            repetition = "".join(table.get_texts("repetition")) or None
            primary_target_group = table.get_texts("primary_target_group")
            digital = "".join(table.get_texts("digital")) or None
            distance_exam = "".join(table.get_texts("distance_exam")) or None
            recording = "".join(table.get_texts("recording")) or None
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
            offered_in = self.extract_offered_in(response)
            for id in offered_in:
                url = f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?abschnittId={id}&semkez={semkez}"
                yield response.follow(url + "&lang=en", self.parse_section)
                yield response.follow(url + "&lang=de", self.parse_section)

            learning_materials = self.extract_learning_materials(response)

            # Get courses
            for k, cols in table.rows:
                course_number = re.match(RE_COURSE_NUMBER, k)
                if course_number:
                    yield self.extract_course(
                        parent_unit=lerneinheitId, semkez=semkez, cols=cols
                    )

            # Print any unknown or missed keys
            if lang == "de":
                for k in table.keys():
                    if (
                        k.strip() == ""
                        or re.match(RE_COURSE_NUMBER, k)
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

            yield Lerneinheit(
                id=lerneinheitId,
                code=unit_number,
                titel=unit_name if lang == "de" else None,
                titelenglisch=unit_name if lang == "en" else None,
                semkez=semkez,
                kreditpunkte=kreditpunkte,
                literatur=literatur if lang == "de" else None,
                literaturenglisch=literatur if lang == "en" else None,
                lernziel=lernziele if lang == "de" else None,
                lernzielenglisch=lernziele if lang == "en" else None,
                inhalt=inhalt if lang == "de" else None,
                inhaltenglisch=inhalt if lang == "en" else None,
                skript=skript if lang == "de" else None,
                skriptenglisch=skript if lang == "en" else None,
                besonderes=besonderes if lang == "de" else None,
                besonderesenglisch=besonderes if lang == "en" else None,
                diplomasupplement=diplomasupplement if lang == "de" else None,
                diplomasupplementenglisch=diplomasupplement if lang == "en" else None,
                angezeigterkommentar=angezeigterkommentar if lang == "de" else None,
                angezeigterkommentaren=angezeigterkommentar if lang == "en" else None,
                sternkollonne=sternkollonne,
                belegungMaxPlatzzahl=belegungMaxPlatzzahl,
                belegungTermin2Wl=belegungTermin2Wl,
                belegungTermin3Ende=belegungTermin3Ende,
                belegungsTerminStart=belegungsTerminStart,
                vorrang=vorrang,
                lehrsprache=lehrsprache,
                Kurzbeschreibung=kurzbeschreibung,
                kompetenzen=kompetenzen if lang == "de" else None,
                kompetenzenenglisch=kompetenzen if lang == "en" else None,
                reglement=reglement,
                hilfsmittel=hilfsmittel,
                prufungzusatzinfo=prufungzusatzinfo,
                prufungsmodus=prufungsmodus,
                prufungssprache=prufungssprache,
                prufungsform=prufungsform,
                prufende=prufende,
                dozierende=dozierende,
                periodizitaet=periodicity,
                repetition=repetition,
                primary_target_group=primary_target_group,
                digital=digital,
                distance_exam=distance_exam,
                recording=recording,
                groups=groups,
                prufungsblock=exam_block_for,
                learning_materials=learning_materials if lang == "de" else None,
                learning_materials_english=learning_materials if lang == "en" else None,
                occurence=occurence,
                general_restrictions=general_restrictions,
                offered_in=offered_in,
            )
        except Exception as e:
            self.logger.error(f"Error parsing lerneinheit {response.url}: {e}")
            with open(".scrapy/database_cache/error_pages.jsonl", "a") as f:
                f.write(
                    f"{json.dumps({'error': str(e), 'traceback': traceback.format_exc(), 'url': response.url})}\n"
                )

    def parse_lecturer(self, response: Response):
        header = response.css("h1::text").get()
        if not header:
            self.logger.error(f"No lecture header found for {response.url}")
            return
        names = header.replace("\n\n", "\n").replace(":", "").split("\n")[:2]
        names = [n.strip() for n in names]

        dozide = re.search(RE_DOZIDE, response.url)
        if not dozide:
            self.logger.error(f"No dozid found for {response.url}")
            return

        golden_owl = any("Golden" in x for x in response.css("img::attr(alt)").getall())

        yield Lehrveranstalter(
            dozide=int(dozide.group(1)),
            vorname=names[0],
            name=names[1],
            golden_owl=golden_owl,
        )

    def parse_section(self, response: Response):
        semkez = re.search(RE_SEMKEZ, response.url)
        id = re.search(RE_ABSCHNITTID, response.url)
        if not semkez or not id:
            self.logger.error(f"No semkez or abschnittId found for {response.url}")
            return
        semkez = semkez.group(1)
        id = int(id.group(1))

        table = Table(response.xpath("//table"))
        parent_level: list[tuple[int, int]] = []
        for key, cols in table.rows:
            if re.match(RE_COURSE_NUMBER, key) or key.startswith("»"):
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
    ) -> Lehrveranstaltung:
        if len(cols) == 5:
            number_sel, title_sel, hours_sel, slots_sel, lecturers_sel = cols
        else:
            number_sel, title_sel, hours_sel, lecturers_sel = cols
            slots_sel = None

        number = number_sel.re_first(RE_COURSE_NUMBER)
        course_type = None
        if number:
            number = number.replace("\xa0", "")
            course_type = CourseTypeEnum[number[-1]]
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
            two_weekly=False,
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
                        two_weekly=day_info.two_weekly,
                    )
                )

        return Lehrveranstaltung(
            unit_id=parent_unit,
            nummer=number,
            titel=title,
            semkez=semkez,
            typ=course_type,
            angezeigterkommentar=comments or None,
            lehrumfang=hours,
            lehrumfangtyp=hours_type,
            timeslots=timeslots,
            dozierende=lecturer_ids,
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
                two_weekly=day_info.two_weekly,
            )
        return groups

    def extract_learning_materials(self, response: Response) -> dict[str, NamedURL]:
        materials: dict[str, NamedURL] = {}
        table = table_under_header(response, ["Lernmaterialien", "Learning Materials"])
        for _, r in table.rows:
            key = r.css("::text").get()
            url = r.css("a::attr(href)").get()
            urlname = r.css("a::text").get()
            if key and url and urlname:
                materials[key] = NamedURL(name=urlname, url=url)
        return materials

    def extract_offered_in(self, response: Response) -> list[int]:
        offered_in: list[int] = []
        table = table_under_header(response, ["Angeboten in", "Offered in"])
        for _, r in table.rows:
            ids = r.re(RE_ABSCHNITTID)
            offered_in.extend([int(i) for i in ids])
        return offered_in


class DayInfo(BaseModel):
    weekday: WeekdayEnum
    date: str | None
    first_half_semester: bool
    second_half_semester: bool
    two_weekly: bool


def get_day_info(day_str: str) -> DayInfo:
    date = re.match(r"(\d{2})\.(\d{2}).", day_str)
    if date:
        date = day_str.rstrip(".")
        return DayInfo(
            weekday=WeekdayEnum.Date,
            date=date,
            first_half_semester=False,
            second_half_semester=False,
            two_weekly=False,
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
        two_weekly="2w" in args,
    )
