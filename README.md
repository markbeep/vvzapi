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

The goal is to scrape every semester to have a full history of all courses. Want to help out? Check out the [scrape locally](#scrape-locally) section and get in contact with me over Discord `@sprutz`. The scraper automatically caches HTML files so that every request only has to ever be executed once. The HTML and error files are all I'm currently interested in.

- [x] `2026S`
- [x] `2025W`
- [x] `2025S`
- [x] `2024W`
- [x] `2024S`
- [ ] `2023W`
- [ ] `2023S`
- [ ] `2022W`
- [ ] `2022S`
- [ ] `2021W`
- [ ] `2021S`
- [ ] `2020W`
- [ ] `2020S`
- [ ] `2019W`
- [ ] `2019S`
- [ ] `2018W`
- [ ] `2018S`
- [ ] `2017W`
- [ ] `2017S`
- [ ] `2016W`
- [ ] `2016S`
- [ ] `2015W`
- [ ] `2015S`
- [ ] `2014W`
- [ ] `2014S`
- [ ] `2013W`
- [ ] `2013S`
- [ ] `2012W`
- [ ] `2012S`
- [ ] `2011W`
- [ ] `2011S`
- [ ] `2010W`
- [ ] `2010S`
- [ ] `2009W`
- [ ] `2009S`
- [ ] `2008W`
- [ ] `2008S`
- [ ] `2007W`
- [ ] `2007S`
- [ ] `2006W`
- [ ] `2006S`
- [ ] `2005W`
- [ ] `2005S`
- [ ] `2004W`
- [ ] `2004S`
- [ ] `2003W`
- [ ] `2003S`
- [ ] `2002W`
- [ ] `2002S`
- [ ] `2001W`

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

#### Run in shell (for debug)

```sh
uv run scrapy shell "<url>"
```

#### Debug spider

```sh
uv run scrapy parse --spider=lectures -c <cb func> "<url>"
uv run scrapy parse --spider=lectures -c parse_unit "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en"
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
