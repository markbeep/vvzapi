#!/bin/sh

# meta_db must succeed before data_db runs: its migration copies the Scrapy cache out of the
# data database, and the data_db migration drops those tables.
set -e

/app/.venv/bin/alembic -n meta_db upgrade heads
/app/.venv/bin/alembic -n data_db upgrade heads

exec /app/.venv/bin/fastapi run api/main.py
