from logging.config import fileConfig
from pathlib import Path

from alembic import context
from api import models
from api.env import Settings
from api.util.db import engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations() -> None:
    Path(Settings().db_path).parent.mkdir(parents=True, exist_ok=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=models.BaseModel.metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations()
