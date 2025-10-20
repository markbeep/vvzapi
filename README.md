# VVZ REST API

Community-made REST API for [VVZ](https://www.vvz.ethz.ch/Vorlesungsverzeichnis)

> [!NOTE]  
> The API is still in it's early stages and very WIP. That means there are currently not as many endpoint options as one might desire.

## Schema

The schema is inspired by the [VVZ Manual](https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18) (starts page 18).

Attributes have been translated to english, dropped (in cases where the value was internal and not visible on VVZ), or additional attributes have been added that were not present in the documentation.

## Semester Status

The goal is to scrape every semester to have a full history of all courses.

- [x] `2025W`
- [x] `2025S`
- [ ] `2024W`
- [ ] `2024S`
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

## Local Development

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

#### Cleanup html cache directory

There might be outdated or unused files in the html cache directories. Using the cleanup script everything that is not needed can be removed:

```sh
uv run scraper/util/cleanup_scrapy.py [--dry-run]
```

### API Server

```sh
uv run fastapi dev api/main.py
```

### Alembic Migrations

#### Create revision

```sh
uv run alembic revision --autogenerate -m "message"
```

#### Run migrations

```sh
uv run alembic upgrade heads
```
