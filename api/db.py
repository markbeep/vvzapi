from sqlalchemy import create_engine
from sqlmodel import Session, text

from api.env import Settings


engine = create_engine(f"sqlite+pysqlite:///{Settings().db_path}")


def get_session():
    with Session(engine) as session:
        session.execute(text("PRAGMA foreign_keys=ON"))  # pyright: ignore[reportDeprecated]
        yield session
