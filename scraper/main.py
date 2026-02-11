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
from api.util.db import get_session
from scraper.env import Settings as EnvSettings
from scraper.spiders.lecturers import LecturersSpider
from scraper.spiders.ratings import RatingsSpider
from scraper.spiders.units import UnitsSpider
from scraper.util.delete_cached import delete_cached


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


settings = get_project_settings()
add_stdout_logging(settings)

process = CrawlerProcess(settings)

# cleanup cache if required
if EnvSettings().enable_rescrape:
    semkezs = delete_cached()
    process.crawl(UnitsSpider, semkezs=semkezs)
    process.crawl(LecturersSpider, semkezs=semkezs)
    process.crawl(RatingsSpider)
else:
    process.crawl(UnitsSpider)
    process.crawl(LecturersSpider)
    process.crawl(RatingsSpider)
process.start()

# vacuum/zip db
logger = logging.getLogger(__name__)

logger.info(f"Vacuuming database into {APISettings().vacuum_path}")
if Path(APISettings().vacuum_path).exists():  # required for VACUUM INTO to work
    Path(APISettings().vacuum_path).unlink()
with next(get_session()) as session:
    session.execute(
        text("VACUUM INTO :vacuum_path"),
        {"vacuum_path": f"{APISettings().vacuum_path}"},
    )
logger.info("Finished vacuuming database")
logger.info(f"Creating database zip file at {APISettings().zip_path}")
with zipfile.ZipFile(APISettings().zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(APISettings().vacuum_path, arcname="database.db")
logger.info("Finished creating database zip file")
db_size = Path(APISettings().db_path).stat().st_size / (1024 * 1024)
vacuum_size = Path(APISettings().vacuum_path).stat().st_size / (1024 * 1024)
zip_size = Path(APISettings().zip_path).stat().st_size / (1024 * 1024)
logger.info(
    f"Database size: {db_size:.2f} MB, vacuum size: {vacuum_size:.2f} MB, zipped size: {zip_size:.2f} MB"
)
logger.info(f"Deleting vacuum file at {APISettings().vacuum_path}")
Path(APISettings().vacuum_path).unlink(missing_ok=True)
logger.info("Finished deleting vacuum file.")
