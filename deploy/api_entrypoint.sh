#!/bin/sh

/app/.venv/bin/alembic -n data_db upgrade heads
/app/.venv/bin/alembic -n meta_db upgrade heads

exec /app/.venv/bin/fastapi run api/main.py
