# VVZ REST API

Community-made REST API for [VVZ](https://www.vvz.ethz.ch/Vorlesungsverzeichnis)

## Quick Start

Head to https://vvzapi.ch and start playing around with the API.

Currently there's barely any documentation. If you want to help out with documentation, you're always open to creating a pull request.

## Search Design

The search is inspired by [Scryfall](https://scryfall.com/).

## Schema

The schema is inspired by the [VVZ Manual](https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18) (starts page 18).

Attributes have been translated to english, dropped (in cases where the value was internal and not visible on VVZ), or additional attributes have been added that were not present in the documentation.

## Semester Status

> [!NOTE]  
> For some reason all semesters 2009-2019 (both S and W) are simply not available. Accessing any of them throws a 403 Forbidden. I wonder if this
> is just some short-term problem or if they'll never come back. Some of the data (for all courses) is available in the
> [Complete Catalogue](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/gesamtverzeichnis.view?lang=en), but I currently do not have any plans
> of parsing data from PDFs.

## Versioning

This project uses semantic versioning. Breaking changes will result in a bump of the major version. There should not be any breaking changes to the endpoints of any endpoints that are the same or lower version than the major version. If the current version is `2.x.x`, the endpoints under `/v1` and `/v2` will not be _intentionally_ updated in a way that would break or completely change their usage. But `/v3` would then still be in prerelease and might change anytime.

---

## Local Development

### Alembic Migrations

Locally a SQLite database is used. Running the migrations automatically creates the database.

#### Run migrations

```sh
uv run alembic upgrade heads
```

#### Create revision

```sh
uv run alembic revision --autogenerate -m "message"
```

### Scraper

#### Create scraper

```sh
uv run scrapy genspider <scraper name> <scraper name>.py
```

#### Run scraper

```sh
uv run -m scraper.main
```

Or for just one of the spiders:

```sh
uv run scrapy crawl units
uv run scrapy crawl lecturers
```

#### Run in shell (for debug)

```sh
uv run scrapy shell "<url>"
```

#### Debug spider

```sh
uv run scrapy parse --spider=units -c <cb func> "<url>"
uv run scrapy parse --spider=units -c parse_start_url "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/sucheLehrangebot.view?lang=de&semkez=2003S&seite=0"
uv run scrapy parse --spider=units -c parse_unit "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en"
```

#### Scrape locally

```sh
docker run \
    -e SEMESTER=W \
    -e START_YEAR=2024 \
    -e END_YEAR=2024 \
    -v $PWD/data:/app/.scrapy \
    markbeep/vvzapi-scraper:nightly
```

In the data directory there'll be a `httpcache` directory containing all crawled HTML files and a `scrapercache` directory containing scraper specific files and potentially a file called `error_pages.jsonl` with errors.

#### Cleanup html cache directory

There might be outdated or unused files in the html cache directories. Using the cleanup script everything that is not needed can be removed. Additionally it can also be used to purposely delete at most `amount` valid cached files from one or more `semester`s that are older than `age-seconds`.

```sh
uv run scraper/util/cleanup_scrapy.py [--dry-run] [--amount <int>] [--age-seconds <int>] [-d <semester>]*
```

### API Server

```sh
uv run fastapi dev api/main.py
```

#### Tailwindcss

```sh
tailwindcss -i api/static/tw.css -o api/static/globals.css --watch
```

### Type Check

```sh
uv run pyright api
uv run pyright scraper
```
