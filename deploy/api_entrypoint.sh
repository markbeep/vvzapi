#!/bin/sh

/app/.venv/bin/alembic upgrade heads

exec /app/.venv/bin/fastapi run api/main.py
