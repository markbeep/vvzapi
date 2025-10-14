import re
from urllib.parse import urljoin
import scrapy
from scrapy.http import Response

from api.models import (
    CatalogueData,
    Course,
    Lecturer,
    PerformanceAssessment,
    SemesterEnum,
    TeachingUnit,
)
from scraper.util.progress import create_progress
from scraper.util.table import TableExtractor, TableRows
from scraper.util.url import delete_url_key, edit_url_key, list_url_params


re_semkez = re.compile(r"semkez=(\w+)")
re_lerneinheitId = re.compile(r"lerneinheitId=(\d+)")
re_lang = re.compile(r"lang=(\w+)")
re_dozide = re.compile(r"dozide=(\d+)")


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
            yield response.follow(search_page_url, self.parse)

        for course in response.css("a::attr(href)").getall():
            if "lerneinheit.view" in course:
                url = edit_url_key(urljoin(response.url, course), "ansicht", ["ALLE"])
                url = delete_url_key(url, "lang")
                yield response.follow(url + "&lang=en", self.parse_course)
                yield response.follow(url + "&lang=de", self.parse_course)

    def parse_course(self, response: Response):
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

        lang = re_lang.search(response.url)
        if not lang:
            lang = "en"
        else:
            lang = lang.group(1)

        # courses
        courses = self.get_courses(response)
        # catalogue data
        catalogue_data = self.get_catalogue_data(response)
        # performance assessment
        performance_assessment = self.get_performance_assessments(response)

        yield TeachingUnit(
            id=int(lerneinheitId),
            number=course_number,
            year=int(semkez[:4]),
            name=course_name,
            semester=SemesterEnum.FS if semkez[-1] == "S" else SemesterEnum.HS,
            text_language=lang,
            # catalogue data
            **catalogue_data.model_dump(),
            # performance assessment
            **performance_assessment.model_dump(),
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

        yield Lecturer(
            id=int(dozide.group(1)),
            firstname=names[0],
            lastname=names[1],
            golden_owl=golden_owl,
        )

    def get_courses(self, response: Response) -> list[Course]:
        table = TableExtractor(response, ["Courses", "Lehrveranstaltungen"])
        part = table.get_parts()[0]
        # print(part.table.css("tr").getall())
        rows = part.table.css("tr:not(:has(> td.td-small))")
        for x in rows:
            number = x.re(r"\d{3}-\d{4}-\d{2}\xa0\w")
            if not number:
                continue
            number = number[0].replace("\xa0", " ")
            comments = "\n".join(
                [t.strip() for t in x.css(".kommentar-lv::text").getall() if t.strip()]
            )

    def get_catalogue_data(self, response: Response):
        table = TableExtractor(response, ["Catalogue data", "Katalogdaten"])
        parts = table.get_parts()
        part = parts[0]
        # There might be multiple parts because of some "INFO" images
        part = part.extend(*parts[1:] if len(parts) > 1 else [])
        rows = part.get_rows()

        for r in rows.others:
            if "Competencies" in " ".join(r.texts()):
                continue
            self.logger.warning(
                f"Unknown catalogue data key in {response.url}: {r.texts()}"
            )

        return CatalogueData(
            abstract=rows.two["abstract"].text(),
            learning_objective=rows.two["learning_objective"].text(),
            content="\n".join(rows.two["content"].texts()),
            notice=rows.two["notice"].text(),
            competencies=rows.two["competencies"].text(),
            lecture_notes=rows.two["lecture_notes"].text(),
            literature=rows.two["literature"].text(),
            other_data=["\n".join(r.texts()) for r in rows.others if r.texts()],
        )

    def get_performance_assessments(self, response: Response):
        table = TableExtractor(
            response, ["Performance assessment", "Leistungskontrolle"]
        )
        parts = table.get_parts()[1:]

        two_semester = TableRows()
        one_semester = TableRows()

        if len(parts) == 2:
            self.logger.info(
                f"Found two semester performance assessment: {response.url}"
            )
            two_semester = parts[0].get_rows()
            parts = parts[1:]
        one_semester = parts[0].get_rows()

        """
        TWO SEMESTER ASSESSMENT
        """
        two_semester_credits = two_semester.two.get("credits")
        two_semester_credits = (
            two_semester_credits.credit() if two_semester_credits else None
        )
        together_with_number = None
        r = two_semester.one["two_semester_course"].re(r"(\d{3}-\d{4}-\d{2}\w) (.+)\n")
        if len(r) == 2:
            together_with_number = r[0]
            together_with_name = r[1]
            self.logger.info(
                f"Found two semester course together with {together_with_number} {together_with_name}: {response.url}"
            )

        """
        ONE SEMESTER ASSESSMENT
        """
        examiner_ids = one_semester.two["examiners"].re(r"dozide=(\d+)")
        examiner_ids = [int(x) for x in examiner_ids]

        return PerformanceAssessment(
            two_semester_credits=two_semester_credits,
            programme_regulations=two_semester.two["regulations"].texts(),
            together_with_number=together_with_number,
            ects_credits=one_semester.two["credits"].credit() or 0.0,
            examiner_ids=examiner_ids,
            assessment_type=one_semester.two["type"].text() or "",
            assessment_language=one_semester.two["assessment_language"].text() or "",
            repetition=one_semester.two["repetition"].text() or "",
            exam_block_of=one_semester.two["exam_block"].texts(),
            mode=one_semester.two["exam_mode"].text(),
            additional_info=one_semester.two["additional_info"].text(),
            written_aids=one_semester.two["written_aids"].text(),
            distance=one_semester.two["distance_exam"].text(),
            digital=one_semester.two["digital"].text(),
            update_note=one_semester.two["to_be_updated"].text(),
            admission_requirement=one_semester.two["admission_requirement"].text(),
            other_assessment=[
                "\n".join(cell.texts()) for cell in one_semester.others if cell.texts()
            ],
        )
