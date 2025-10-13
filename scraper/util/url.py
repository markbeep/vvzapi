from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def edit_url_key(url: str, key: str, value: list[str]):
    url_res = urlparse(url)
    query = parse_qs(url_res.query, keep_blank_values=True)
    query[key] = value
    url_res = url_res._replace(query=urlencode(query, True))
    return urlunparse(url_res)


def delete_url_key(url: str, key: str):
    url_res = urlparse(url)
    query = parse_qs(url_res.query, keep_blank_values=True)
    query.pop(key)
    url_res = url_res._replace(query=urlencode(query, True))
    return urlunparse(url_res)
