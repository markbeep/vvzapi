# pyright: reportExplicitAny=false,reportAny=false

from typing import Any, override
from scrapy.spiders import CrawlSpider
from scrapy.utils.log import SpiderLoggerAdapter


class KeywordLoggerAdapter(SpiderLoggerAdapter):
    """A logger adapter which adds the 'keyword' attribute to log records."""

    @override
    def process(self, msg: str, kwargs: Any):
        # append key=value pairs from extra to the message (sorted for deterministic order)
        if extra := kwargs.get("extra", {}):
            pairs = [f"{k}={str(extra[k])}" for k in sorted(extra)]
            msg = f"{msg} {' '.join(pairs)}"
        return msg, kwargs


class KeywordLoggerSpider(CrawlSpider):
    @property
    @override
    def logger(self):
        logger = super().logger
        return KeywordLoggerAdapter(logger, {"spider": self})
