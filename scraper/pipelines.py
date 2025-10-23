import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from scrapy import Spider
from sqlmodel import Session, select

from api.models import (
    Course,
    CourseLecturerLink,
    LearningUnit,
    Lecturer,
    Level,
    Section,
    UnitExaminerLink,
    UnitLecturerLink,
    UnitSectionLink,
)
from api.util import db
from scraper.util.mappings import UnitDepartmentMapping, UnitLevelMapping

CACHE_PATH = "scrapercache"
SECTION_LINK = f".scrapy/{CACHE_PATH}/unit_section_link.jsonl"
DEP_LINK = f".scrapy/{CACHE_PATH}/unit_dep_link.jsonl"
LEVEL_LINK = f".scrapy/{CACHE_PATH}/unit_level_link.jsonl"
LECTURER_LINK = f".scrapy/{CACHE_PATH}/unit_lecturer_link.jsonl"
EXAMINER_LINK = f".scrapy/{CACHE_PATH}/unit_examiner_link.jsonl"
COURSE_LINK = f".scrapy/{CACHE_PATH}/course_lecturer_link.jsonl"


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


def add_section_link(
    session: Session, item: UnitSectionLink, /, commit: bool = True
) -> bool:
    old = session.get(
        UnitSectionLink,
        (item.unit_id, item.section_id),
    )
    if old:
        return True
    sec = session.get(Section, item.section_id)
    unit = session.get(LearningUnit, item.unit_id)
    if sec and unit:
        session.add(item)
        if commit:
            session.commit()
        return True
    return False


def add_examiner_link(
    session: Session, item: UnitExaminerLink, /, commit: bool = True
) -> bool:
    old = session.get(
        UnitExaminerLink,
        (item.unit_id, item.lecturer_id),
    )
    if old:
        return True
    lecturer = session.get(Lecturer, item.lecturer_id)
    unit = session.get(LearningUnit, item.unit_id)
    if lecturer and unit:
        session.add(item)
        if commit:
            session.commit()
        return True
    return False


def add_lecturer_link(
    session: Session, item: UnitLecturerLink, /, commit: bool = True
) -> bool:
    old = session.get(
        UnitLecturerLink,
        (item.unit_id, item.lecturer_id),
    )
    if old:
        return True
    lecturer = session.get(Lecturer, item.lecturer_id)
    unit = session.get(LearningUnit, item.unit_id)
    if lecturer and unit:
        session.add(item)
        if commit:
            session.commit()
        return True
    return False


def add_course_link(
    session: Session, item: CourseLecturerLink, /, commit: bool = True
) -> bool:
    old = session.get(
        CourseLecturerLink,
        (item.course_id, item.lecturer_id),
    )
    if old:
        return True
    lecturer = session.get(Lecturer, item.lecturer_id)
    course = session.get(Course, item.course_id)
    if lecturer and course:
        session.add(item)
        if commit:
            session.commit()
        return True
    return False


class DatabasePipeline:
    def open_spider(self, spider: Spider):
        self.session = next(db.get_session())
        self.logger = spider.logger
        Path(f".scrapy/{CACHE_PATH}").mkdir(parents=True, exist_ok=True)
        Path(SECTION_LINK).touch(exist_ok=True)
        Path(DEP_LINK).touch(exist_ok=True)
        Path(LEVEL_LINK).touch(exist_ok=True)
        Path(LECTURER_LINK).touch(exist_ok=True)
        Path(EXAMINER_LINK).touch(exist_ok=True)
        Path(COURSE_LINK).touch(exist_ok=True)

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
        elif isinstance(item, UnitSectionLink):
            if not add_section_link(self.session, item):
                append(SECTION_LINK, item)
            return item
        elif isinstance(item, UnitExaminerLink):
            if not add_examiner_link(self.session, item):
                append(EXAMINER_LINK, item)
            return item
        elif isinstance(item, UnitLecturerLink):
            if not add_lecturer_link(self.session, item):
                append(LECTURER_LINK, item)
            return item
        elif isinstance(item, CourseLecturerLink):
            if not add_course_link(self.session, item):
                append(COURSE_LINK, item)
            return item
        else:
            return item

        if old is None:
            self.session.add(item)
            self.session.commit()

        return item

    def close_spider(self, spider: Spider):
        """
        Add links after hopefully all base models have been added
        """
        for line in iter_lines(SECTION_LINK):
            link = UnitSectionLink.model_validate_json(line)
            if add_section_link(self.session, link, commit=False):
                self.logger.debug(
                    f"Adding UnitSectionLink: unit_id={link.unit_id}, section_id={link.section_id}"
                )
        Path(SECTION_LINK).unlink(missing_ok=True)

        for line in iter_lines(EXAMINER_LINK):
            link = UnitExaminerLink.model_validate_json(line)
            if add_examiner_link(self.session, link, commit=False):
                self.logger.debug(
                    f"Adding UnitExaminerLink: unit_id={link.unit_id}, lecturer_id={link.lecturer_id}"
                )
        Path(EXAMINER_LINK).unlink(missing_ok=True)

        for line in iter_lines(LECTURER_LINK):
            link = UnitLecturerLink.model_validate_json(line)
            if add_lecturer_link(self.session, link, commit=False):
                self.logger.debug(
                    f"Adding UnitLecturerLink: unit_id={link.unit_id}, lecturer_id={link.lecturer_id}"
                )
        Path(LECTURER_LINK).unlink(missing_ok=True)

        for line in iter_lines(COURSE_LINK):
            link = CourseLecturerLink.model_validate_json(line)
            if add_course_link(self.session, link, commit=False):
                self.logger.debug(
                    f"Adding CourseLecturerLink: course_number={link.course_id}, lecturer_id={link.lecturer_id}"
                )
        Path(COURSE_LINK).unlink(missing_ok=True)

        """
        Update mappings after hopefully all LearningUnits have been added
        """
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
