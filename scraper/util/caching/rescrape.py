"""
Cache layout

All pages are cached in an sqlite DB with DBHTTPCache.

If enable_rescrape is enabled:
- At most rescrape_amount unit
pages of the last two semesters are rescraped.
- seit=0 pages are rescraped if older than an hour
"""

from time import time

from sqlmodel import col, distinct, or_, select

from api.models import HTTPCache, LearningUnit
from api.util.db import get_meta_session, get_session
from scraper.env import Settings

settings = Settings()
enable_rescrape = Settings().enable_rescrape
rescrape_amount = Settings().rescrape_amount


def get_last_semesters(n: int) -> list[str]:
    with next(get_session()) as session:
        semkezs = session.exec(
            select(distinct(LearningUnit.semkez))
            .order_by(col(LearningUnit.semkez).desc())
            .limit(n)
        ).all()
    return list(semkezs)


RESCRAPE_SEMKEZS = get_last_semesters(1) if enable_rescrape else None

# gets the outdated urls and any seite=0 urls
clauses = []
oldest_urls = set[str]()
flagged = set[str]()
if RESCRAPE_SEMKEZS is not None:
    clauses = or_(
        *[
            col(HTTPCache.url).contains(f"semkez={semkez}")
            for semkez in RESCRAPE_SEMKEZS
        ]
    )
    with next(get_meta_session()) as session:
        oldest_urls = set(
            session.exec(
                select(HTTPCache.url)
                .order_by(col(HTTPCache.scraped_at))
                .where(clauses)
                .limit(rescrape_amount)
            ).all()
        )

        # seite=0 pages
        seite0_urls = session.exec(
            select(HTTPCache.url)
            .where(
                clauses,
                col(HTTPCache.url).contains("seite=0"),
                col(HTTPCache.scraped_at) < int(time()) - 3600,  # older than an hour
            )
            .order_by(col(HTTPCache.scraped_at))
            .limit(50)
        ).all()
        oldest_urls.update(seite0_urls)


def should_rescrape(url: str):
    return enable_rescrape and url in oldest_urls
