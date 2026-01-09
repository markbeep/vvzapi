from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def edit_url_key(url: str, key: str, value: list[str]) -> str:
    url_res = urlparse(url)
    query = parse_qs(url_res.query, keep_blank_values=True)
    query[key] = value
    url_res = url_res._replace(query=urlencode(query, True))
    return urlunparse(url_res)


def delete_url_key(url: str, key: str) -> str:
    url_res = urlparse(url)
    query = parse_qs(url_res.query, keep_blank_values=True)
    query.pop(key)
    url_res = url_res._replace(query=urlencode(query, True))
    return urlunparse(url_res)


def list_url_params(url: str) -> dict[str, list[str]]:
    url_res = urlparse(url)
    return parse_qs(url_res.query, keep_blank_values=True)


def sort_url_params(url: str) -> str:
    url_res = urlparse(url)
    query = parse_qs(url_res.query, keep_blank_values=True)
    sorted_query = dict(sorted(query.items()))
    url_res = url_res._replace(query=urlencode(sorted_query, True))
    return urlunparse(url_res)
