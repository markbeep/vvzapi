# pyright: reportAny=false, reportExplicitAny=false

import logging
import sys
import zipfile
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings
from sqlmodel import text

from api.env import Settings as APISettings
from api.util.db import engine, get_dump_table_names, get_session
from api.util.materialize import update_materialized_views
from scraper.analytics import record_scrape_run
from scraper.spiders.lecturers import LecturersSpider
from scraper.spiders.ratings import RatingsSpider
from scraper.spiders.units import UnitsSpider

logger = logging.getLogger(__name__)


def add_stdout_logging(settings: Settings):
    format = settings.get("LOG_FORMAT")
    if not format:
        return
    formatter = logging.Formatter(format)
    level_name = settings.get("LOG_LEVEL", "INFO")

    sh = logging.StreamHandler(sys.stdout)
    # We can theoretically have different log levels for stdout and file
    sh.setLevel(level_name)
    sh.setFormatter(formatter)

    root = logging.getLogger()
    root.addHandler(sh)


def crawl():
    settings = get_project_settings()
    add_stdout_logging(settings)
    process = CrawlerProcess(settings)
    process.crawl(UnitsSpider)
    process.crawl(LecturersSpider)
    process.crawl(RatingsSpider)
    process.start()


def update_materialized_view():
    logger.info("Finished scraping data, updating materialized tables")
    with next(get_session()) as session:
        update_materialized_views(session)


def export_database():
    export_path = APISettings().export_path
    logger.info(f"Exporting course-related tables into {export_path}")
    Path(export_path).unlink(missing_ok=True)  # ATTACH target must be empty
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("ATTACH DATABASE :path AS export"), {"path": export_path})
        for table in get_dump_table_names():
            # identifiers cannot be bound; names come from DUMP_TABLES
            conn.execute(
                text(f'CREATE TABLE export."{table}" AS SELECT * FROM main."{table}"')
            )
        conn.execute(text("DETACH DATABASE export"))
    logger.info("Finished exporting database")
    logger.info(f"Creating database zip file at {APISettings().zip_path}")
    with zipfile.ZipFile(APISettings().zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(export_path, arcname="database.db")
    logger.info("Finished creating database zip file")
    db_size = Path(APISettings().db_path).stat().st_size / (1024 * 1024)
    export_size = Path(export_path).stat().st_size / (1024 * 1024)
    zip_size = Path(APISettings().zip_path).stat().st_size / (1024 * 1024)
    logger.info(
        f"Database size: {db_size:.2f} MB, export size: {export_size:.2f} MB, zipped size: {zip_size:.2f} MB"
    )
    logger.info(f"Deleting export file at {export_path}")
    Path(export_path).unlink(missing_ok=True)
    logger.info("Finished deleting export file.")


def vacuum():
    logger.info(f"Vacuuming database at {APISettings().db_path}")
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("VACUUM"))
    logger.info("Finished vacuuming database")


if __name__ == "__main__":
    crawl()
    record_scrape_run()
    update_materialized_view()
    export_database()
    vacuum()
