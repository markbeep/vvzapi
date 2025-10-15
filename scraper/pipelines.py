import pathlib
from typing import Any
from scrapy import Spider

from api import db
from api.new_models.lerneinheit import Lerneinheit
from api.new_models.lehrveranstalter import Lehrveranstalter

CACHE_PATH = "database_cache"


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())
        pathlib.Path(f".scrapy/{CACHE_PATH}").mkdir(parents=True, exist_ok=True)
        with open(f".scrapy/{CACHE_PATH}/courses.jsonl", "w") as f:
            pass
        with open(f".scrapy/{CACHE_PATH}/course_lecturer_relations.jsonl", "w") as f:
            pass

    def process_item(self, item: Any, spider: Spider):
        if isinstance(item, Lerneinheit):
            old = self.session.get(Lerneinheit, item.id)
            if old:
                old.overwrite_with(item)
                self.session.add(old)
                self.session.commit()
                return item
        elif isinstance(item, Lehrveranstalter):
            old = self.session.get(Lehrveranstalter, item.dozide)
        else:
            return item

        if old is None:
            self.session.add(item)
            self.session.commit()

        return item

    def close_spider(self, spider: Spider):
        self.session.close()
