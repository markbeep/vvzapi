import time
from sqlmodel import col, distinct, select
from api.models import LastCleanup, LearningUnit
from api.util.db import get_session
from scraper.env import Settings
from scraper.util.cleanup_scrapy import cleanup_scrapy


def delete_cached():
    print("Checking if cached files should be deleted...")
    with next(get_session()) as session:
        last_cleanup = session.exec(
            select(LastCleanup).order_by(col(LastCleanup.timestamp).desc()).limit(1)
        ).first()
        last_cleanup_time = last_cleanup.timestamp if last_cleanup else 0

        # prevent cleaning up if pod is crash-looping
        now = int(time.time())
        if now - last_cleanup_time < 22 * 3600:
            print(
                "Last cleanup was performed less than 22 hours ago, skipping cleanup."
            )
            return

        last_semesters = session.exec(
            select(distinct(LearningUnit.semkez))
            .order_by(col(LearningUnit.semkez).desc())
            .limit(2)
        ).all()
        if not last_semesters:
            print("No semesters found in database, skipping cleanup.")
            return

        print(f"Performing cleanup of cached files for semesters: {last_semesters}")

        cleanup_scrapy(
            dry_run=True,
            delete_cached_semesters=list(last_semesters),
            amount=Settings().rescrape_amount,
            age_seconds=Settings().rescrape_age_seconds * 3600,
        )

        last_cleanup = LastCleanup(timestamp=now)
        session.add(last_cleanup)
