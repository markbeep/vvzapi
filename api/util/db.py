from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlmodel import Session, text
from sqlmodel.ext.asyncio.session import AsyncSession

from api.env import Settings
from api.models import DUMP_TABLES
from api.util.pydantic_type import json_serializer

# SQLite allows a single writer at a time. A busy timeout makes a connection wait for
# the lock instead of immediately raising "database is locked", which is what the
# scraper would otherwise hit while the API is reading.
_BUSY_TIMEOUT = 30  # seconds


def _use_wal(dbapi_connection: SQLiteConnection, _connection_record: object) -> None:
    """Put the database in WAL mode so readers no longer block on the scraper's writer."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


engine = create_engine(
    f"sqlite+pysqlite:///{Settings().db_path}",
    json_serializer=json_serializer,
    connect_args={"timeout": _BUSY_TIMEOUT},
)

aengine = create_async_engine(
    f"sqlite+aiosqlite:///{Settings().db_path}",
    json_serializer=json_serializer,
    pool_size=20,
    max_overflow=30,
    connect_args={"timeout": _BUSY_TIMEOUT},
)

meta_engine = create_engine(
    f"sqlite+pysqlite:///{Settings().meta_db_path}",
    json_serializer=json_serializer,
    connect_args={"timeout": _BUSY_TIMEOUT},
)

ameta_engine = create_async_engine(
    f"sqlite+aiosqlite:///{Settings().meta_db_path}",
    json_serializer=json_serializer,
    pool_size=20,
    max_overflow=30,
    connect_args={"timeout": _BUSY_TIMEOUT},
)

for _engine in (engine, aengine.sync_engine, meta_engine, ameta_engine.sync_engine):
    event.listen(_engine, "connect", _use_wal)


def get_session():
    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


async def aget_session():
    async with AsyncSession(aengine) as session:
        await session.execute(text("pragma mmap_size=30000000000"))
        await session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


def get_meta_session():
    with Session(meta_engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))
        yield session


async def aget_meta_session():
    async with AsyncSession(ameta_engine) as session:
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
