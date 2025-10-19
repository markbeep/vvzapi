from typing import Literal
import scrapy
from scrapy.http import Response

from api.models.lecturer import Lecturer
from scraper.env import Settings
from scraper.util.regex_rules import RE_DOZIDE


def get_urls(year: int, semester: Literal["W", "S"]):
    # seite=0 shows all results in one page
    url = f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheDozierende.view?lang=de&semkez={year}{semester}&seite=0"
    return [url]


class LecturersSpider(scrapy.Spider):
    name = "lecturers"
    start_urls = [
        url
        for year in range(Settings().start_year, Settings().end_year + 1)
        for semester in Settings().read_semesters()
        for url in get_urls(year, semester)
    ]

    def parse(self, response: Response):
        rows = response.css("tr")
        for row in rows:
            dozid = row.css("a::attr(href)").re_first(RE_DOZIDE)
            surname = row.css("a::text").get()
            name = row.css("b::text").get()
            if dozid and surname and name:
                yield Lecturer(
                    id=int(dozid),
                    surname=surname,
                    name=name,
                )
