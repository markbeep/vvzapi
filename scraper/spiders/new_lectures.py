import re
from urllib.parse import urljoin
import scrapy
from scrapy.http import Response

# from api.models import Lecturer
from api.new_models.lerneinheit import Lerneinheit
from api.new_models.lehrnveranstalter import Lehrveranstalter
from scraper.util.keymap import get_key
from scraper.util.progress import create_progress
from scraper.util.table import Table, TableExtractor, TableRows
from scraper.util.url import delete_url_key, edit_url_key, list_url_params


re_semkez = re.compile(r"semkez=(\w+)")
re_lerneinheitId = re.compile(r"lerneinheitId=(\d+)")
re_lang = re.compile(r"lang=(\w+)")
re_dozide = re.compile(r"dozide=(\d+)")


class LecturesSpider(scrapy.Spider):
    name = "new_lectures"
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
            yield response.follow(search_page_url, self.parse)

        for course in response.css("a::attr(href)").getall():
            if "lerneinheit.view" in course:
                url = edit_url_key(urljoin(response.url, course), "ansicht", ["ALLE"])
                url = delete_url_key(url, "lang")
                yield response.follow(url + "&lang=en", self.parse_lerneinheit)
                yield response.follow(url + "&lang=de", self.parse_lerneinheit)

    def parse_lerneinheit(self, response: Response):
        # lecturers might be listed here under examiners, but not under courses.
        # By checking all lecturers on the course page, we ensure that we get all of them.
        for course in response.css("a::attr(href)").getall():
            if "dozent.view" in course:
                for param in list_url_params(course).keys():
                    if param != "dozide" and param != "semkez":
                        course = delete_url_key(course, param)
                yield response.follow(course, self.parse_lecturer)

        course_title = response.css(
            "section#contentContainer div#contentTop h1::text"
        ).extract_first()
        if not course_title:
            self.logger.error(f"No course title found for {response.url}")
            return
        course_title = course_title.split("\n")
        course_number = course_title[0].replace("\xa0", "").strip()
        course_name = " ".join(course_title[1:]).strip()

        semkez = re_semkez.search(response.url)
        if not semkez:
            self.logger.error(f"No semkez found for {response.url}")
            return
        semkez = semkez.group(1)

        lerneinheitId = re_lerneinheitId.search(response.url)
        if not lerneinheitId:
            self.logger.warning(f"No lerneinheitId found for {response.url}")
            lerneinheitId = "unknown"
        else:
            lerneinheitId = lerneinheitId.group(1)
        lerneinheitId = int(lerneinheitId)

        lang = re_lang.search(response.url)
        if not lang:
            lang = "en"
        else:
            lang = lang.group(1)

        # courses
        # for item in self.get_courses(response, lerneinheitId):
        #     yield item
        # catalogue data
        # catalogue_data = self.get_catalogue_data(response)
        # # performance assessment
        # performance_assessment = self.get_performance_assessments(response)
        # # offered in
        # offered_in = self.get_offered_in(response)

        # for examiner_id in performance_assessment.examiner_ids:
        #     yield ExamLecturerRelations(
        #         teaching_unit_id=lerneinheitId, lecturer_id=examiner_id
        #     )

        table = Table(response)

        kreditpunkte = table.find_last("credits")
        if kreditpunkte is not None:
            kreditpunkte = kreditpunkte[1].css("::text").get()
            if kreditpunkte is not None:
                kreditpunkte = float(kreditpunkte.split("\xa0")[0])
        url = table.find("url")
        if url is not None:
            url = url[1].css("a::attr(href)").get()
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
        belegungTermin2Wl = table.re_first("waiting_list", r"(\d{2}\.\d{2}\.\d{4})")
        belegungTermin3Ende = table.re_first(
            "registration_end", r"(\d{2}\.\d{2}\.\d{4})"
        )
        belegungsTerminStart = table.re_first(
            "registration_start", r"(\d{2}\.\d{2}\.\d{4})"
        )
        vorrang = "".join(table.get_texts("priority")) or None

        keys = table.keys()
        for k in keys:
            if (
                k.strip() == ""
                or re.match(r"\d{3}-\d{4}-\d{2}", k)
                or "zusätzlichen Belegungseinschränkungen" in k
                or "additional restrictions" in k
            ):
                continue
            if get_key(k) == "other":
                with open(".scrapy/database_cache/unknown_keys.jsonl", "a") as f:
                    f.write(f'{{"key": "{k}", "url": "{response.url}"}}\n')

        yield Lerneinheit(
            id=lerneinheitId,
            code=course_number,
            titel=course_name if lang == "de" else None,
            titelenglisch=course_name if lang == "en" else None,
            semkez=semkez,
            kreditpunkte=kreditpunkte,
            url=url,
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
        )

    def parse_lecturer(self, response: Response):
        header = response.css("h1::text").get()
        if not header:
            self.logger.error(f"No lecture header found for {response.url}")
            return
        names = header.replace("\n\n", "\n").replace(":", "").split("\n")[:2]
        names = [n.strip() for n in names]

        dozide = re_dozide.search(response.url)
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
