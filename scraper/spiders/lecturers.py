import re
from typing import Literal, Any, override

from scrapy.http import Response

from api.models import Lecturer
from scraper.env import Settings
from scraper.util.logging import KeywordLoggerSpider
from scraper.util.regex_rules import RE_DOZIDE, RE_SEMKEZ


def get_urls(year: int, semester: Literal["W", "S"]):
    # seite=0 shows all results in one page
    url = f"https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheDozierende.view?lang=de&semkez={year}{semester}&seite=0"
    return [url]


class LecturersSpider(KeywordLoggerSpider):
    name = "lecturers"

    def __init__(self, semkezs: list[str] | None = None, *a: Any, **kw: Any):
        if semkezs is not None:
            self.start_urls = [
                url
                for semkez in semkezs
                for url in get_urls(int(semkez[:-1]), "S" if semkez[-1] == "S" else "W")
            ]
        else:
            self.start_urls = [
                url
                for year in range(Settings().start_year, Settings().end_year + 1)
                for semester in Settings().read_semesters()
                for url in get_urls(year, semester)
            ]
        super().__init__(*a, **kw)

    @override
    def parse_start_url(self, response: Response, **kwargs: Any):
        semkez = re.search(RE_SEMKEZ, response.url)
        if not semkez:
            self.logger.error(
                "Could not extract semkez from URL", extra={"url": response.url}
            )
            return
        semkez = semkez.group(1)
        self.logger.info(
            "Parsing lecturers page", extra={"semkez": semkez, "url": response.url}
        )

        rows = response.css("tr")
        self.logger.info(
            "Found lecturer rows", extra={"count": len(rows), "semkez": semkez}
        )
        count = 0
        for row in rows:
            dozid = row.css("a::attr(href)").re_first(RE_DOZIDE)
            surname = row.css("a::text").get()
            name = row.css("b::text").get()
            if dozid and surname and name:
                count += 1
                yield Lecturer(
                    id=int(dozid),
                    surname=surname,
                    name=name,
                )
        self.logger.info(
            "Extracted lecturers", extra={"count": count, "semkez": semkez}
        )
