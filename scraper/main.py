from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraper.spiders.lecturers import LecturersSpider
from scraper.spiders.lectures import LecturesSpider

process = CrawlerProcess(get_project_settings())
process.crawl(LecturesSpider)
process.crawl(LecturersSpider)
process.start()
