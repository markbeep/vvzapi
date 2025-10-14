import pathlib
from typing import Any
from scrapy import Spider
from sqlalchemy.dialects.sqlite import insert

from api import db
from api.models import Course, CourseLecturerRelations, Lecturer, TeachingUnit

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
        if isinstance(item, TeachingUnit):
            self.session.exec(
                insert(TeachingUnit)
                .values(**item.model_dump())
                .on_conflict_do_update(set_=item.model_dump())
            )
            self.session.commit()
        elif isinstance(item, Lecturer):
            self.session.exec(
                insert(Lecturer)
                .values(**item.model_dump())
                .on_conflict_do_update(set_=item.model_dump())
            )
            self.session.commit()

        # Course and CourseLecturerRelations have foreign keys. So we only add them at the end when all lecturers/units have been added
        elif isinstance(item, Course):
            with open(f".scrapy/{CACHE_PATH}/courses.jsonl", "a") as f:
                f.write(item.model_dump_json() + "\n")
        elif isinstance(item, CourseLecturerRelations):
            with open(
                f".scrapy/{CACHE_PATH}/course_lecturer_relations.jsonl", "a"
            ) as f:
                f.write(item.model_dump_json() + "\n")

        else:
            return item

        return item.model_dump()

    def close_spider(self, spider: Spider):
        with open(f".scrapy/{CACHE_PATH}/courses.jsonl", "r") as f:
            insert_data = [Course.model_validate_json(line) for line in f]
            print(f"Inserting {len(insert_data)} courses into the database")
            if insert_data:
                self.session.exec(
                    insert(Course)
                    .values([data.model_dump() for data in insert_data])
                    .on_conflict_do_nothing()
                )
                self.session.commit()

        with open(f".scrapy/{CACHE_PATH}/course_lecturer_relations.jsonl", "r") as f:
            insert_data = [
                CourseLecturerRelations.model_validate_json(line) for line in f
            ]
            print(
                f"Inserting {len(insert_data)} course-lecturer relations into the database"
            )
            if insert_data:
                self.session.exec(
                    insert(CourseLecturerRelations)
                    .values([data.model_dump() for data in insert_data])
                    .on_conflict_do_nothing()
                )
                self.session.commit()

        self.session.close()
