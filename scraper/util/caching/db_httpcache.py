from email.parser import Parser
from pathlib import Path
from typing import final, override

import yaml
from rich import print
from scrapy import Request, Spider
from scrapy.extensions import httpcache
from scrapy.http import Response
from scrapy.responsetypes import responsetypes
from scrapy.settings import BaseSettings
from sqlmodel import Session

from api.models import HTTPCache
from api.util.db import meta_engine
from scraper.util.caching.rescrape import should_rescrape
from scraper.util.url import normalized_url


@final
class DBHTTPCache(httpcache.FilesystemCacheStorage):
    def __init__(self, settings: BaseSettings | None):
        if settings:
            super().__init__(settings)

    @override
    def open_spider(self, spider: Spider) -> None:
        self.logger = spider.logger

    @override
    def close_spider(self, spider: Spider) -> None:
        pass

    @override
    def retrieve_response(self, spider: Spider, request: Request) -> Response | None:
        url = self._normalize_url(request.url)

        if should_rescrape(url):
            self.logger.info(
                "URL marked for rescraping, skipping cache",
                extra={"url": url},
            )
            return None

        with Session(meta_engine.connect()) as session:
            entry = session.get(HTTPCache, url)
        if not entry:
            return None
        if entry.flagged:
            self.logger.info(
                "URL flagged for rescraping, skipping cache",
                extra={"url": url},
            )
            return None

        headers = (
            {k.encode(): v.encode() for k, v in entry.headers.items()}
            if entry.headers
            else {}
        )

        respcls = responsetypes.from_args(
            headers=headers,
            url=url,
            body=entry.body,
        )
        return respcls(
            url=url,
            headers=headers,
            status=entry.status_code,
            body=entry.body or b"",
        )

    @override
    def store_response(
        self, spider: Spider, request: Request, response: Response
    ) -> None:
        self.store(request.url, response, None)

    def store(self, url: str, response: Response, timestamp: float | None):
        if response.status == 302:
            return

        url = self._normalize_url(url)
        headers: dict[str, str] = dict(response.headers.to_unicode_dict())
        with Session(meta_engine.connect()) as session:
            entry = HTTPCache(
                url=url,
                status_code=response.status,
                headers=headers,
                body=response.body,
            )
            if timestamp is not None:
                entry.scraped_at = int(timestamp)

            session.merge(entry)
            session.commit()

    def _normalize_url(self, url: str) -> str:
        return normalized_url(url)


@final
class Migrator:
    """Used to migrate httpcache to dbhttpcache above"""

    def __init__(self, cachedir: str) -> None:
        self.cachedir = cachedir
        self.cache = DBHTTPCache(None)

    def migrate(self):
        for dir in self._walk():
            try:
                with open(dir / "meta", "r") as f:
                    # yaml allows us to open the invalid formatted json file
                    data = yaml.load(f, Loader=yaml.SafeLoader)  # pyright: ignore[reportAny]
                url: str = data.get("url", "")  # pyright: ignore[reportAny]
                timestamp: float | None = data.get("timestamp")  # pyright: ignore[reportAny]
                status: int = data.get("status", 0)  # pyright: ignore[reportAny]
                with open(dir / "response_body", "rb") as f:
                    body = f.read()
                with open(dir / "response_headers", "r") as f:
                    parsed = Parser().parse(f)
                    headers = dict(parsed.items())
                self._add(url, timestamp, status, headers, body)
                print(f"Migrated {url} from {dir}")
            except Exception as e:
                print(f"[red]Failed to migrate from {dir}: {e}[/red]")

    def _add(
        self,
        url: str,
        timestamp: float | None,
        status: int,
        headers: dict[str, str],
        body: bytes,
    ):
        response = Response(url=url, status=status, headers=headers, body=body)
        self.cache.store(url, response, timestamp)

    def _walk(self):
        cachedir = Path(self.cachedir)
        for spiderdir in cachedir.iterdir():
            if not spiderdir.is_dir():
                continue
            for shortdir in spiderdir.iterdir():
                if not shortdir.is_dir():
                    continue
                for requestdir in shortdir.iterdir():
                    if not requestdir.is_dir():
                        continue
                    yield requestdir


if __name__ == "__main__":
    migrator = Migrator(".scrapy/httpcache")
    migrator.migrate()
