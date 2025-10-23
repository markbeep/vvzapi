import json


def append_error(error: str, **kwargs: str):
    with open(".scrapy/scrapercache/error_pages.jsonl", "a") as f:
        f.write(f"{json.dumps({'error': error, **kwargs})}\n")
