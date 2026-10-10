#!/bin/sh

/app/.venv/bin/alembic upgrade heads

exec /app/.venv/bin/python -m scraper.main
