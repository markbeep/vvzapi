from typing import Any
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import SpiderLoggerAdapter


class KeywordLoggerAdapter(SpiderLoggerAdapter):
    """A logger adapter which adds the 'keyword' attribute to log records."""

    def process(self, msg: str, kwargs: Any):
        # append key=value pairs from extra to the message (sorted for deterministic order)
        if extra := kwargs.get("extra", {}):
            pairs = [f"{k}={str(extra[k])}" for k in sorted(extra)]
            msg = f"{msg} {' '.join(pairs)}"
        return msg, kwargs


class KeywordLoggerSpider(CrawlSpider):
    @property
    def logger(self):
        from scraper.util.logging import KeywordLoggerAdapter

        logger = super().logger
        return KeywordLoggerAdapter(logger, {"spider": self})
