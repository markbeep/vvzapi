from typing import Any
from scrapy import Spider
from sqlmodel import select

from api import db
from api.new_models.lehrveranstaltungen import Lehrveranstaltung
from api.new_models.lerneinheit import Lerneinheit
from api.new_models.lehrveranstalter import Lehrveranstalter
from api.new_models.section import Section

CACHE_PATH = "database_cache"


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())

    def process_item(self, item: Any, spider: Spider):
        if isinstance(item, Lerneinheit):
            old = self.session.get(Lerneinheit, item.id)
            if old:
                old.overwrite_with(item)
                self.session.add(old)
                self.session.commit()
                return item
        elif isinstance(item, Section):
            old = self.session.get(Section, item.id)
            if old:
                old.overwrite_with(item)
                self.session.add(old)
                self.session.commit()
                return item
        elif isinstance(item, Lehrveranstalter):
            old = self.session.get(Lehrveranstalter, item.dozide)
        elif isinstance(item, Lehrveranstaltung):
            old = self.session.exec(
                select(Lehrveranstaltung).where(
                    Lehrveranstaltung.nummer == item.nummer,
                    Lehrveranstaltung.semkez == item.semkez,
                )
            ).first()
        else:
            return item

        if old is None:
            self.session.add(item)
            self.session.commit()

        return item

    def close_spider(self, spider: Spider):
        self.session.close()
