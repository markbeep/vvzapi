from typing import Any, final, override
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, TypeAdapter
from scrapy.http import Request, Response

from api.models import Rating
from scraper.util.logging import KeywordLoggerSpider


class _Rating(BaseModel):
    CourseNumber: str
    Recommended: float
    Engaging: float
    Difficulty: float
    Effort: float
    Resources: float


_RatingsResponse = TypeAdapter(list[_Rating])


@final
class RatingsSpider(KeywordLoggerSpider):
    name: str = "ratings"
    start_urls = ["https://cr.vsos.ethz.ch/getAllRatingsAvg"]

    @override
    def parse_start_url(self, response: Response, **_: Any):  # pyright: ignore[reportExplicitAny]
        if not response.request:
            self.logger.debug("No request found for response, skipping")
            return
        url = urlparse(response.request.url)
        current_page = parse_qs(url.query).get("page", [1])[0]

        if response.text == "null":
            self.logger.info("Reached end of ratings at", extra={"page": current_page})
            return

        yield Request(
            url=f"https://cr.vsos.ethz.ch/getAllRatingsAvg?page={int(current_page) + 1}"
        )

        ratings = _RatingsResponse.validate_json(response.text)
        self.logger.info(
            "Scraped ratings for", extra={"page": current_page, "count": len(ratings)}
        )

        for rating in ratings:
            yield Rating(
                course_number=rating.CourseNumber,
                recommended=rating.Recommended,
                engaging=rating.Engaging,
                difficulty=rating.Difficulty,
                effort=rating.Effort,
                resources=rating.Resources,
            )
