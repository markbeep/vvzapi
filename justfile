# https://just.systems

alias d := dev

dev:
    uv run fastapi dev api/main.py

alias m := migrate

migrate:
    uv run alembic upgrade heads

alias s := scrape

scrape:
    uv run -m scraper.main

alias tw := tailwind

tailwind:
    tailwindcss -i api/static/tw.css -o api/static/globals.css --watch

# update all uv packages
upgrade:
    uvx uv-upgrade

test:
    uv run basedpyright
    uv run djlint api/templates/ --lint
    uv run djlint api/templates/ --check

lighthouse PATH="":
    lighthouse http://localhost:8000{{ PATH }} --output-path=localhost.html

alias dau := debug_all_units

debug_all_units SEMKEZ:
    uv run scrapy parse --spider=units -c parse_start_url "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lang=de&semkez={{ SEMKEZ }}&seite=0"

alias du := debug_single_unit

debug_single_unit SEMKEZ UNITID:
    uv run scrapy parse --spider=units -c parse_unit "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez={{ SEMKEZ }}&ansicht=ALLE&lerneinheitId={{ UNITID }}&lang=en"

alias dal := debug_all_lecturers

debug_all_lecturers SEMKEZ:
    uv run scrapy parse --spider=lecturers -c parse_start_url "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheDozierende.view?lang=de&semkez={{ SEMKEZ }}&seite=0"

jaeger:
    docker run --rm --name jaeger \
      -p 16686:16686 \
      -p 4317:4317 \
      -p 4318:4318 \
      -p 5778:5778 \
      -p 9411:9411 \
      cr.jaegertracing.io/jaegertracing/jaeger:2.15.0

influxdb:
    docker run --rm -p 8181:8181 \
      influxdb:3-core influxdb3 serve \
        --node-id=my-node-0 \
        --object-store=file \
        --data-dir=/var/lib/influxdb3/data \
        --plugin-dir=/var/lib/influxdb3/plugins
