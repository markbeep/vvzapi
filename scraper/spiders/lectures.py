import re
import scrapy
import scrapy.http

re_semkez = re.compile(r"semkez=(\w)+")
re_lerneinheitId = re.compile(r"lerneinheitId=(\d+)")
re_lang = re.compile(r"lang=(\d+)")


class LecturesSpider(scrapy.Spider):
    name = "lectures"
    start_urls = [
        "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?search=on&semkez=2025W&studiengangTyp=&deptId=&studiengangAbschnittId=&lerneinheitstitel=&lerneinheitscode=&famname=&rufname=&wahlinfo=&lehrsprache=&periodizitaet=&kpRange=0%2C999"
    ]

    def parse(self, response: scrapy.http.Response):
        for course in response.css("a::attr(href)").getall():
            if "/Vorlesungsverzeichnis/lerneinheit.view" in course:
                yield response.follow(course, self.parse_course)
            # elif "/Vorlesungsverzeichnis/sucheLehrangebot.view" in course:
            #     yield response.follow(course, self.parse)

    def parse_course(self, response: scrapy.http.Response):
        if "lang=en" not in response.url:
            yield response.follow(response.url + "&lang=en", self.parse_course)

        course_title = response.css(
            "section#contentContainer div#contentTop h1::text"
        ).extract_first()
        if not course_title:
            self.logger.warning(f"No course title found for {response.url}")
            return
        course_title = course_title.split("\n")
        course_id = course_title[0].replace("\xa0", "").strip()
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
            "id": course_id,
            "title": course_name,
            "semkez": semkez,
            "lerneinheitId": lerneinheitId,
            "lang": lang,
        }
