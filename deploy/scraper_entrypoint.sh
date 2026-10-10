#!/bin/sh

# meta_db must succeed before data_db runs: its migration copies the Scrapy cache out of the
# data database, and the data_db migration drops those tables. The scraper is the component
# that relies on the cache, so a half-applied upgrade must stop the container instead of
# starting against a cache that was just deleted.
set -e

/app/.venv/bin/alembic -n meta_db upgrade heads
/app/.venv/bin/alembic -n data_db upgrade heads

exec /app/.venv/bin/python -m scraper.main
