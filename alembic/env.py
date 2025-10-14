import pathlib
from logging.config import fileConfig

from alembic import context
from api import models
from api.db import engine
from api.env import Settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = models.BaseModel.metadata


def run_migrations() -> None:
    pathlib.Path(Settings().db_path).parent.mkdir(parents=True, exist_ok=True)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
