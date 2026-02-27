from collections.abc import MutableMapping
from logging.config import fileConfig
from pathlib import Path
from typing import Literal

from sqlalchemy import Table
from sqlalchemy.sql.schema import SchemaItem
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


# SQLModel ignores the metadata= kwarg and puts all tables into SQLModel.metadata.
# We distinguish which tables belong to which DB by walking subclasses instead.
_base_table_names = _get_table_names(BaseModel)
_meta_table_names = _get_table_names(MetadataModel)

IncludeNameType = Literal[
    "schema",
    "table",
    "column",
    "index",
    "unique_constraint",
    "foreign_key_constraint",
]
ParentNamesType = MutableMapping[
    Literal["schema_name", "table_name", "schema_qualified_table_name"], str | None
]


def _include_name_base(
    name: str | None, type_: IncludeNameType, _parent_names: ParentNamesType
) -> bool:
    if type_ == "table":
        return name in _base_table_names
    return True


def _include_name_meta(
    name: str | None, type_: IncludeNameType, _parent_names: ParentNamesType
) -> bool:
    if type_ == "table":
        return name in _meta_table_names
    return True


def _include_object_base(
    object_: SchemaItem,
    name: str | None,
    type_: str,
    _reflected: bool,
    _compare_to: SchemaItem | None,
) -> bool:
    if type_ == "table":
        if isinstance(object_, Table):
            return object_.name in _base_table_names
        return name in _base_table_names if name else False
    return True


def _include_object_meta(
    object_: SchemaItem,
    name: str | None,
    type_: str,
    _reflected: bool,
    _compare_to: SchemaItem | None,
) -> bool:
    if type_ == "table":
        if isinstance(object_, Table):
            return object_.name in _meta_table_names
        return name in _meta_table_names if name else False
    return True


def run_migrations() -> None:
    if "".join(config.get_version_locations_list() or "").endswith("meta_versions"):
        # metadata db
        Path(Settings().meta_db_path).parent.mkdir(parents=True, exist_ok=True)
        with meta_engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=SQLModel.metadata,
                render_as_batch=True,
                include_name=_include_name_meta,
                include_object=_include_object_meta,
            )

            with context.begin_transaction():
                context.run_migrations()

    else:
        # data db
        Path(Settings().db_path).parent.mkdir(parents=True, exist_ok=True)
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=SQLModel.metadata,
                render_as_batch=True,
                include_name=_include_name_base,
                include_object=_include_object_base,
            )

            with context.begin_transaction():
                context.run_migrations()


run_migrations()
