## Notes

- Lecturer information is listed in `robots.txt`. But we need to access the lecturer page to get the full name of a lecturer for course search reasons. We do not store any other Lecturer information.

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
