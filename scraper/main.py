from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

import logging
import sys

from scraper.spiders.lecturers import LecturersSpider
from scraper.spiders.units import UnitsSpider


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
process.crawl(UnitsSpider)
process.crawl(LecturersSpider)
process.start()
