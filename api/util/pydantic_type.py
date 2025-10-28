import json
from typing import Any, Sequence

from fastapi.encoders import jsonable_encoder
import sqlalchemy as sa
from pydantic import BaseModel, parse_obj_as  # pyright: ignore[reportDeprecated]
from pydantic.json import pydantic_encoder
from sqlalchemy.dialects.postgresql import JSONB


class PydanticType[T: BaseModel](sa.types.TypeDecorator[sa.JSON()]):
    impl = sa.types.JSON

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

    def process_result_value(self, value: Any, dialect: sa.Dialect):  # pyright: ignore[reportIncompatibleMethodOverride]
        # Concerning the deprecation warning:
        # parse_obj_as works for Basemodels as well as list/dicts.
        # The "new" pydantic.TypeAdapter.validate_python does not.
        return parse_obj_as(self.pydantic_type, value) if value else None  # pyright: ignore[reportDeprecated]


def json_serializer(*args: Any, **kwargs: Any) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)
