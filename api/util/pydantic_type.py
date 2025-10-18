import json
from typing import Any, Sequence

from fastapi.encoders import jsonable_encoder
import sqlalchemy as sa
from pydantic import BaseModel, parse_obj_as
from pydantic.json import pydantic_encoder
from sqlalchemy.dialects.postgresql import JSONB


class PydanticType[T: BaseModel](sa.types.TypeDecorator):
    impl = sa.types.JSON

    def __init__(
        self,
        pydantic_type: type[T] | type[Sequence[T]] | type[dict[str, list[T]]],
    ):
        super().__init__()
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(sa.JSON())

    def process_bind_param(self, value: Any, dialect: sa.Dialect):
        return jsonable_encoder(value) if value else None

    def process_result_value(self, value: Any, dialect: sa.Dialect):
        return parse_obj_as(self.pydantic_type, value) if value else None


def json_serializer(*args, **kwargs) -> str:
    return json.dumps(*args, default=pydantic_encoder, **kwargs)
