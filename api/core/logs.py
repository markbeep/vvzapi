# pyright: reportExplicitAny=false,reportAny=false

import logging
from typing import Any, override


class KeywordLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Render `extra` as `key=value` pairs appended to the message.

    Mirrors the scraper's `scraper.util.logging.KeywordLoggerAdapter` so both sides of the
    application log in the same `message key=value` style.
    """

    @override
    def process(self, msg: str, kwargs: Any):
        if extra := kwargs.get("extra", {}):
            # sorted for a deterministic order
            pairs = [f"{key}={extra[key]}" for key in sorted(extra)]
            msg = f"{msg} {' '.join(pairs)}"
        return msg, kwargs


def quiet_httpx_request_logs() -> None:
    """Silence `httpx`'s one-line-per-request INFO logging, process-wide.

    The ClickHouse writer (used by the API and by the scraper) emits one such line per insert,
    which drowns out the application logs, so the whole `httpx` logger is raised to WARNING.
    That deliberately covers the other `httpx` clients too (the flag webhook and the Plausible
    event poster log one line per flag/pageview). Their failures still surface: httpx reports
    errors above INFO.
    """
    logging.getLogger("httpx").setLevel(logging.WARNING)
