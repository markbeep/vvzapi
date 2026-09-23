"""Buffered ClickHouse writer for analytics events.

ClickHouse strongly prefers few large inserts over many small ones (every insert
creates a part), so events are queued in memory and flushed as a single
`INSERT ... FORMAT JSONEachRow` per table on a short interval.

Analytics must never break a request: enqueueing is synchronous and cheap, and a
failing or missing ClickHouse instance drops events instead of raising.
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx

from api.env import Settings

logger = logging.getLogger(__name__)


class ClickHouseWriter:
    def __init__(self) -> None:
        self._queues: dict[str, list[dict[str, object]]] = {}
        self._task: asyncio.Task[None] | None = None
        self._lock: asyncio.Lock | None = None
        self._failing: bool = False

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def enqueue(self, table: str, row: dict[str, object]) -> None:
        clickhouse = Settings().clickhouse
        if not clickhouse.url:
            return
        queue = self._queues.setdefault(table, [])
        if len(queue) >= clickhouse.queue_max:
            if not self._failing:
                logger.warning("clickhouse queue full, dropping analytics events")
                self._failing = True
            return
        queue.append(row)
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._flush_loop())

    async def _flush_loop(self) -> None:
        while True:
            await asyncio.sleep(Settings().clickhouse.flush_interval_seconds)
            try:
                await self.flush()
            except Exception as error:  # noqa: BLE001 - analytics must not crash
                if not self._failing:
                    logger.warning("clickhouse flush failed: %s", error)
                    self._failing = True

    async def flush(self) -> None:
        """Send everything queued so far. Safe to call concurrently."""
        max_rows = Settings().clickhouse.max_rows_per_insert
        async with self._get_lock():
            pending = {table: rows for table, rows in self._queues.items() if rows}
            for table in pending:
                self._queues[table] = []
        for table, rows in pending.items():
            for start in range(0, len(rows), max_rows):
                await self._insert(table, rows[start : start + max_rows])

    async def _insert(self, table: str, rows: list[dict[str, object]]) -> None:
        settings = Settings().clickhouse
        if not rows or not settings.url:
            return
        payload = "\n".join(
            json.dumps(row, separators=(",", ":"), default=str) for row in rows
        )
        url = settings.url
        params = {
            "database": settings.database,
            "query": f"INSERT INTO {table} FORMAT JSONEachRow",
        }
        async with httpx.AsyncClient() as client:
            if settings.password:
                response = await client.post(
                    url,
                    params=params,
                    content=payload.encode(),
                    auth=(settings.user, settings.password),
                    timeout=10,
                )
            else:
                response = await client.post(
                    url,
                    params=params,
                    content=payload.encode(),
                    timeout=10,
                )
            if response.status_code >= 400:
                # Surface ClickHouse's own message: schema drift is otherwise
                # invisible because analytics failures must not bubble up.
                raise RuntimeError(
                    f"clickhouse insert into {table} failed: {response.status_code} {response.text[:400]}"
                )
        if self._failing:
            logger.info("clickhouse writes recovered")
            self._failing = False


writer = ClickHouseWriter()
