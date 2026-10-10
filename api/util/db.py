from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlmodel import Session, text
from sqlmodel.ext.asyncio.session import AsyncSession

from api.env import Settings
from api.models import DUMP_TABLES
from api.util.pydantic_type import json_serializer

engine = create_engine(
    f"sqlite+pysqlite:///{Settings().db_path}", json_serializer=json_serializer
)

aengine = create_async_engine(
    f"sqlite+aiosqlite:///{Settings().db_path}",
    json_serializer=json_serializer,
    pool_size=20,
    max_overflow=30,
)


def get_session():
    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


async def aget_session():
    async with AsyncSession(aengine) as session:
        await session.execute(text("pragma mmap_size=30000000000"))
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


def get_dump_table_names() -> list[str]:
    """Table names served by the /dump export, see DUMP_TABLES."""
    # getattr: SQLModel declares __tablename__ as an InstrumentedAttribute, while the
    # runtime value of a `table=True` model is always the declared name string.
    return sorted(
        table_name
        for cls in DUMP_TABLES
        if isinstance(table_name := getattr(cls, "__tablename__", None), str)
    )
