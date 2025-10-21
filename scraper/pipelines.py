from pathlib import Path
from typing import Any
from pydantic import BaseModel
from scrapy import Spider
from sqlmodel import select
import json

from api.util import db
from api.models import Course
from api.models import LearningUnit, Level, Section, UnitSectionLink
from api.models import Lecturer
from scraper.util.types import UnitDepartmentMapping, UnitLevelMapping

CACHE_PATH = "scrapercache"
SECTION_LINK = f".scrapy/{CACHE_PATH}/unit_section_link.jsonl"
DEP_LINK = f".scrapy/{CACHE_PATH}/unit_dep_link.jsonl"
LEVEL_LINK = f".scrapy/{CACHE_PATH}/unit_level_link.jsonl"


def append(file_path: str, item: BaseModel):
    with open(file_path, "a") as f:
        f.write(item.model_dump_json() + "\n")


def append_json(file_path: str, data: dict):
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")


def iter_lines(file_path: str):
    with open(file_path, "r") as f:
        for line in f:
            yield line


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())
        self.logger = spider.logger
        Path(f".scrapy/{CACHE_PATH}").mkdir(parents=True, exist_ok=True)
        Path(SECTION_LINK).touch(exist_ok=True)
        Path(DEP_LINK).touch(exist_ok=True)
        Path(LEVEL_LINK).touch(exist_ok=True)

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
                    Course.number == item.number,
                    Course.semkez == item.semkez,
                )
            ).first()
        elif isinstance(item, UnitSectionLink):
            old = self.session.get(
                UnitSectionLink,
                (item.unit_id, item.section_id),
            )
            if old:
                return item
            sec = self.session.get(Section, item.section_id)
            unit = self.session.get(LearningUnit, item.unit_id)
            if sec and unit:
                self.session.add(item)
                self.session.commit()
            else:
                append(SECTION_LINK, item)
            return item
        elif isinstance(item, UnitDepartmentMapping):
            unit = self.session.get(LearningUnit, item.unit_id)
            if unit:
                unit.department = item.department
                self.session.add(unit)
                self.session.commit()
            else:
                append(DEP_LINK, item)
            return item
        elif isinstance(item, UnitLevelMapping):
            unit = self.session.get(LearningUnit, item.unit_id)
            if unit:
                unit.levels = [Level(level) for level in unit.levels]
                if item.level not in unit.levels:
                    unit.levels.append(item.level)
                    self.session.add(unit)
            else:
                append(LEVEL_LINK, item)
            return item
        else:
            return item

        if old is None:
            self.session.add(item)
            self.session.commit()

        return item

    def close_spider(self, spider: Spider):
        for line in iter_lines(SECTION_LINK):
            link = UnitSectionLink.model_validate_json(line)
            existing_link = self.session.get(
                UnitSectionLink,
                (link.unit_id, link.section_id),
            )
            if existing_link is None:
                self.logger.debug(
                    f"Adding UnitSectionLink: unit_id={link.unit_id}, section_id={link.section_id}"
                )
                self.session.add(link)
        Path(SECTION_LINK).unlink(missing_ok=True)

        for line in iter_lines(DEP_LINK):
            mapping = UnitDepartmentMapping.model_validate_json(line)
            unit = self.session.get(LearningUnit, mapping.unit_id)
            if unit:
                self.logger.debug(
                    f"Updating LearningUnit id={mapping.unit_id} with department={mapping.department}"
                )
                unit.department = mapping.department
                self.session.add(unit)
        Path(DEP_LINK).unlink(missing_ok=True)

        for line in iter_lines(LEVEL_LINK):
            mapping = UnitLevelMapping.model_validate_json(line)
            unit = self.session.get(LearningUnit, mapping.unit_id)
            if unit:
                self.logger.debug(
                    f"Updating LearningUnit id={mapping.unit_id} with level={mapping.level}"
                )
                unit.levels = [Level(level) for level in unit.levels]
                if mapping.level not in unit.levels:
                    unit.levels.append(mapping.level)
                    self.session.add(unit)
        Path(LEVEL_LINK).unlink(missing_ok=True)

        self.session.commit()
        self.session.close()
