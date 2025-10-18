from typing import Any
from scrapy import Spider
from sqlmodel import select

from api.util import db
from api.models.course import Course
from api.models.learning_unit import LearningUnit
from api.models.lecturer import Lecturer
from api.models.section import Section

CACHE_PATH = "database_cache"


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())

    def process_item(self, item: Any, spider: Spider):
        if isinstance(item, LearningUnit):
            old = self.session.get(LearningUnit, item.id)
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
        elif isinstance(item, Lecturer):
            old = self.session.get(Lecturer, item.id)
        elif isinstance(item, Course):
            old = self.session.exec(
                select(Course).where(
                    Course.code == item.code,
                    Course.semkez == item.semkez,
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
