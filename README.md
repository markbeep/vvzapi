# VVZ REST API

Community-made REST API for [VVZ](https://www.vvz.ethz.ch/Vorlesungsverzeichnis)

> [!NOTE]  
> The API is still in it's early stages and very WIP. That means there are currently not as many endpoint options as one might desire.

## Scraper

#### Create scraper

```sh
uv run scrapy genspider <scraper name> <scraper name>.py
```

#### Run scraper

```sh
uv run scrapy crawl lectures
```

#### Run in shell (for debug)

```sh
uv run scrapy shell "<url>"
```

#### Debug spider

```sh
uv run scrapy parse --spider=lectures -c <cb func> "<url>"
uv run scrapy parse --spider=lectures -c parse_lerneinheit "https://www.vvz.ethz.ch/Vorlesungsverzeichnis/lerneinheit.view?semkez=2025W&ansicht=ALLE&lerneinheitId=192945&lang=en"
```

## Alembic

#### Create revision

```sh
uv run alembic revision --autogenerate -m "message"
```

#### Run migrations

```sh
uv run alembic upgrade heads
```

## API

```sh
uv run fastapi dev api/main.py
```

## Schema

[VVZ Schema](https://www.bi.id.ethz.ch/soapvvz-2023-1/manual/SoapVVZ.pdf#page=18) (starts page 18)
