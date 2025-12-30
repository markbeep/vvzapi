import json
from enum import Enum
from typing import Any, Sequence, cast

import sqlalchemy as sa
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, parse_obj_as
from pydantic.json import pydantic_encoder  # pyrefly: ignore[missing-module-attribute]
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import TypeDecorator


class PydanticType[T: BaseModel](TypeDecorator[sa.JSON]):
    impl = sa.JSON

    def __init__(
        self,
        pydantic_type: type[T] | type[Sequence[T]] | type[dict[str, list[T]]],
    ):
        super().__init__()
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect: sa.Dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value: Any, dialect: sa.Dialect):
        return jsonable_encoder(value) if value else None

    def process_result_value(  # pyrefly: ignore[bad-override]
        self, value: Any, dialect: sa.Dialect
    ):
        # Concerning the deprecation warning:
        # parse_obj_as works for Basemodels as well as list/dicts.
        # The "new" pydantic.TypeAdapter.validate_python does not.
        return (
            parse_obj_as(
                self.pydantic_type,  # pyrefly: ignore[bad-argument-type]
                value,
            )
            if value
            else None
        )


def json_serializer(*args: Any, **kwargs: Any) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)


class EnumList[T: Enum](TypeDecorator[sa.JSON]):
    impl = sa.JSON
    cache_ok = True

    def __init__(self, enum_cls: type[T]):
        super().__init__()
        self.enum_cls = enum_cls

    def process_bind_param(self, value: Any | None, dialect: Any) -> list[Any] | None:
        if value is None:
            return None
        if not isinstance(value, list):
            return value
        return [
            item.value if hasattr(item, "value") else item
            for item in cast(list[Any], value)
        ]

    def process_result_value(  # pyrefly: ignore[bad-override]
        self,
        value: list[Any] | None,
        dialect: Any,
    ) -> list[T] | None:
        if value is None:
            return []
        converter = getattr(self.enum_cls, "get", self.enum_cls)
        return [converter(item) for item in value]
