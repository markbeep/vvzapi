from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import MetaData
from sqlmodel import SQLModel

from alembic import context
from api.env import Settings
from api.models import BaseModel, MetadataModel
from api.util.db import engine, meta_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _get_table_names(base_cls: type) -> set[str]:
    """Recursively collect __tablename__ from all table-model subclasses."""
    names: set[str] = set()
    for cls in base_cls.__subclasses__():
        tablename = getattr(cls, "__tablename__", None)
        if isinstance(tablename, str) and hasattr(cls, "__table__"):
            names.add(tablename)
        names |= _get_table_names(cls)
    return names


def _build_filtered_metadata(table_names: set[str]) -> MetaData:
    """Build a new MetaData containing only the specified tables from SQLModel.metadata.

    SQLModel ignores the metadata= kwarg and registers all tables into a single
    shared SQLModel.metadata. To make Alembic correctly detect additions, changes,
    AND removals per-database, we construct a filtered MetaData that only contains
    the tables belonging to that database. This way Alembic sees exactly which
    tables should exist and can generate drops for any that are missing.
    """
    filtered = MetaData()
    for name, table in SQLModel.metadata.tables.items():
        if name in table_names:
            table.to_metadata(filtered)
    return filtered


# Distinguish which tables belong to which DB by walking model subclasses.
_base_table_names = _get_table_names(BaseModel)
_meta_table_names = _get_table_names(MetadataModel)

_base_metadata = _build_filtered_metadata(_base_table_names)
_meta_metadata = _build_filtered_metadata(_meta_table_names)


def run_migrations() -> None:
    if "".join(config.get_version_locations_list() or "").endswith("meta_versions"):
        # metadata db
        Path(Settings().meta_db_path).parent.mkdir(parents=True, exist_ok=True)
        with meta_engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=_meta_metadata,
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()

    else:
        # data db
        Path(Settings().db_path).parent.mkdir(parents=True, exist_ok=True)
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=_base_metadata,
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()


run_migrations()
