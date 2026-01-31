# https://just.systems

alias d := dev
alias m := migrate
alias s := scrape
alias tw := tailwind

dev:
    uv run fastapi dev api/main.py

migrate:
    uv run alembic upgrade heads

scrape:
    uv run -m scraper.main

tailwind:
    tailwindcss -i api/static/tw.css -o api/static/globals.css --watch
