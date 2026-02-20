from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlmodel import Session, text
from sqlmodel.ext.asyncio.session import AsyncSession

from api.env import Settings
from api.util.pydantic_type import json_serializer

engine = create_engine(
    f"sqlite+pysqlite:///{Settings().db_path}", json_serializer=json_serializer
)

aengine = create_async_engine(
    f"sqlite+aiosqlite:///{Settings().db_path}", json_serializer=json_serializer
)


def get_session():
    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


async def aget_session():
    async with AsyncSession(aengine) as session:
        yield session
