from pathlib import Path
from typing import Any
from scrapy import Spider
from sqlmodel import select

from api.util import db
from api.models.course import Course
from api.models.learning_unit import (
    LearningUnit,
    Section,
    UnitSectionLink,
    UnitTypeEnum,
)
from api.models.lecturer import Lecturer

CACHE_PATH = "database_cache"


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())
        Path(f".scrapy/{CACHE_PATH}").mkdir(parents=True, exist_ok=True)
        Path(f".scrapy/{CACHE_PATH}/unit_section_link.jsonl").touch(exist_ok=True)

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
        elif isinstance(item, UnitSectionLink):
            with open(f".scrapy/{CACHE_PATH}/unit_section_link.jsonl", "a") as f:
                f.write(item.model_dump_json() + "\n")
            return item
        else:
            return item

        if old is None:
            self.session.add(item)
            self.session.commit()

        return item

    def close_spider(self, spider: Spider):
        with open(f".scrapy/{CACHE_PATH}/unit_section_link.jsonl", "r") as f:
            for line in f:
                link = UnitSectionLink.model_validate_json(line)
                link.type = (
                    UnitTypeEnum(link.type) if link.type else None
                )  # fixes the enum type
                existing_link = self.session.get(
                    UnitSectionLink,
                    (link.unit_id, link.section_id),
                )
                if existing_link is None:
                    self.session.add(link)
        self.session.commit()
        Path(f".scrapy/{CACHE_PATH}/unit_section_link.jsonl").unlink(missing_ok=True)

        self.session.close()
