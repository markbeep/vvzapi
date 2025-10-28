from sqlalchemy import create_engine
from sqlmodel import Session, text

from api.env import Settings
from api.util.pydantic_type import json_serializer  # pyright: ignore[reportUnknownVariableType]


engine = create_engine(
    f"sqlite+pysqlite:///{Settings().db_path}", json_serializer=json_serializer
)


def get_session():
    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))  # pyright: ignore[reportDeprecated]
        yield session
