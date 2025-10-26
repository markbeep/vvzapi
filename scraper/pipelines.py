import traceback
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from scrapy import Spider
from sqlmodel import select

from api.models import (
    Course,
    CourseLecturerLink,
    LearningUnit,
    Lecturer,
    Level,
    Overwriteable,
    Section,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
    UnitTypeLegends,
)
from api.util import db
from scraper.util.mappings import UnitDepartmentMapping, UnitLevelMapping
from scraper.util.scrapercache import CACHE_PATH

DEP_LINK = CACHE_PATH / "unit_dep_link.jsonl"
LEVEL_LINK = CACHE_PATH / "unit_level_link.jsonl"


def append(file_path: Path, item: BaseModel):
    with open(file_path, "a") as f:
        f.write(item.model_dump_json() + "\n")


def iter_lines(file_path: Path):
    with open(file_path, "r") as f:
        for line in f:
            yield line


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())
        self.logger = spider.logger
        CACHE_PATH.mkdir(parents=True, exist_ok=True)

    def process_item(self, item: Any, spider: Spider):
        try:
            # first check if they are mappings. Dept/level mappings update
            # existing unit models
            if isinstance(item, UnitDepartmentMapping):
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

            # Then we process models that get added to the database
            if isinstance(item, (LearningUnit, Section, Lecturer, UnitTypeLegends)):
                old = self.session.get(type(item), item.id)
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
            elif isinstance(item, (UnitExaminerLink, UnitLecturerLink)):
                old = self.session.get(
                    type(item),
                    (item.unit_id, item.lecturer_id),
                )
            elif isinstance(item, CourseLecturerLink):
                old = self.session.get(
                    CourseLecturerLink,
                    (item.course_number, item.course_semkez, item.lecturer_id),
                )
            else:
                self.logger.error("Unknown item type", extra={"item": item})
                return item

            if not old:
                self.session.add(item)
                self.session.commit()
            elif isinstance(old, Overwriteable):
                # we assume old has been modified in place
                # TODO: log what was changed
                old.overwrite_with(item)
                self.session.add(old)
                self.session.commit()

            return item
        except Exception as e:
            self.logger.error(
                "Error adding item",
                extra={
                    "item": item,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

    def close_spider(self, spider: Spider):
        """
        Update mappings after hopefully all LearningUnits have been added
        """
        if DEP_LINK.exists():
            for line in iter_lines(DEP_LINK):
                mapping = UnitDepartmentMapping.model_validate_json(line)
                unit = self.session.get(LearningUnit, mapping.unit_id)
                if unit:
                    self.logger.debug(
                        f"Updating LearningUnit id={mapping.unit_id} with department={mapping.department}"
                    )
                    unit.department = mapping.department
                    self.session.add(unit)
                else:
                    self.logger.error(
                        f"Failed to update LearningUnit id={mapping.unit_id} with department={mapping.department}"
                    )
                    append(DEP_LINK.with_suffix(".failed"), mapping)
            DEP_LINK.unlink()

        if LEVEL_LINK.exists():
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
                else:
                    self.logger.error(
                        f"Failed to update LearningUnit id={mapping.unit_id} with level={mapping.level}"
                    )
                    append(LEVEL_LINK.with_suffix(".failed"), mapping)
            LEVEL_LINK.unlink()

        self.session.commit()
        self.session.close()
