from typing import Any
from scrapy import Spider

from api.models import Lecturer, TeachingUnit


class DatabasePipeline:
    def process_item(self, item: Any, spider: Spider):
        if isinstance(item, TeachingUnit):
            ...
        elif isinstance(item, Lecturer):
            ...
        else:
            return None

        return item.model_dump()
