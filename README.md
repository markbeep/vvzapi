# VVZ REST API

Community-made REST API for [VVZ](https://www.vvz.ethz.ch/Vorlesungsverzeichnis)

> [!CAUTION]  
> The API is still in alpha and very WIP. That means any endpoints or data-structures are prone to changing and will likely not be fully backwards compatible. _There also might just not be any data or data could be missing in the current state._
>
> Wait for version >=1 (meaning api is at `/api/v1`) for a more stable experience or play around with `/api/v0` with the risks in mind.

## Quick Start

Head to https://vvzapi.ch and start playing around with the API.

Currently there's barely any documentation. If you want to help out with documentation, you're always open to creating a pull request.

## Schema

The schema is inspired by the [VVZ Manual](https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18) (starts page 18).

Attributes have been translated to english, dropped (in cases where the value was internal and not visible on VVZ), or additional attributes have been added that were not present in the documentation.

## Semester Status

> [!NOTE]  
> Every available semester has been cached (2001W-2008W and 2018S-2026S). Thank you everyone for helping out!
> Now it's only a matter of time before the DB models are finalized and all the data is pushed to be available on the API endpoints.
>
> For some reason all semesters 2009-2017 (both S and W) are simply not available. Accessing any of them throws a 403 Forbidden. I wonder if this
> is just some short-term problem or if they'll never come back. Some of the data (for all courses) is available in the
> [Complete Catalogue](https://www.vvz.ethz.ch/Vorlesungsverzeichnis/gesamtverzeichnis.view?lang=en), but I currently do not have any plans
> of parsing data from PDFs.

## Future Plans

- [x] Replicate VVZ filters
- [ ] Flag to display results in the exact same order as on VVZ
- [ ] Dump endpoints. Get a dump of a whole semester (JSON or SQlite) so that you can more efficiently go over data locally without having to bombard the API.
- [ ] Semantic search
- [ ] ML-based tagging from the lecture abstracts and descriptions. Would allow for easily showing related lectures.

## Local Development

### Alembic Migrations

Locally a SQLite database is used. Running the migrations automatically creates the database.

> [!CAUTION]
> While in alpha, migration files might be merged or recreated, potentially breaking any local state.

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

There might be outdated or unused files in the html cache directories. Using the cleanup script everything that is not needed can be removed:

```sh
uv run scraper/util/cleanup_scrapy.py [--dry-run]
```

### API Server

```sh
uv run fastapi dev api/main.py
```

### Type Check

```sh
uv run pyright api
uv run pyright scraper
```
