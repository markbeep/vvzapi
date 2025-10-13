import re
from urllib.parse import urljoin
import scrapy
import scrapy.http

from api.models import Lecturer
from scraper.util.progress import create_progress
from scraper.util.url import delete_url_key, edit_url_key


re_semkez = re.compile(r"semkez=(\w+)")
re_lerneinheitId = re.compile(r"lerneinheitId=(\d+)")
re_lang = re.compile(r"lang=(\w+)")
re_dozide = re.compile(r"dozide=(\d+)")


class LecturesSpider(scrapy.Spider):
    name = "lectures"
    start_urls = [
        "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lerneinheitscode=&deptId=&famname=&unterbereichAbschnittId=&lerneinheitstitel=&rufname=&kpRange=0,999&lehrsprache=&bereichAbschnittId=&semkez=2025W&studiengangAbschnittId=&studiengangTyp=&ansicht=1&lang=en&katalogdaten=&wahlinfo="
        "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lerneinheitscode=&deptId=&famname=&unterbereichAbschnittId=&lerneinheitstitel=&rufname=&kpRange=0,999&lehrsprache=&bereichAbschnittId=&semkez=2025W&studiengangAbschnittId=&studiengangTyp=&ansicht=1&lang=en&katalogdaten=&wahlinfo=&strukturAus=on"
    ]

    def parse(self, response: scrapy.http.Response):
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

    def parse_course(self, response: scrapy.http.Response):
        # lecturers might be listed here as examiners instead of only giving courses
        for course in response.css("a::attr(href)").getall():
            if "dozent.view" in course:
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

        yield {
            "number": course_number,
            "title": course_name,
            "semkez": semkez,
            "lerneinheitId": int(lerneinheitId),
            "lang": lang,
        }

    def parse_lecturer(self, response: scrapy.http.Response):
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

        yield Lecturer(id=int(dozide.group(1)), firstname=names[0], lastname=names[1])
