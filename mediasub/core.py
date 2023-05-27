from __future__ import annotations

import asyncio
import datetime as dt
import logging
import pathlib
from typing import TYPE_CHECKING, Any, Callable, Iterable

import aiosqlite
import httpx

from ._logger import BraceMessage as __
from ._logger import setup_logger
from .errors import SourceDown
from .models.base import HistoryContent, Source

if TYPE_CHECKING:
    from .types import Callback, RecentT_co, ReturnT, SourceT

setup_logger("mediasub")
logger = logging.getLogger(__name__)


class MediaSub:
    default_timeout = 300  # in seconds

    def __init__(self, db_path: str):
        self._db = Database(db_path)
        self._client = httpx.AsyncClient()
        self._timeouts: dict[str, dt.datetime] = {}
        self._bound_callbacks: dict[Source[Any, Any, Any], list[Callback[Any, Any, Any]]] = {}
        self._running_tasks: list[asyncio.Task[Any]] = []

    @property
    def sources(self) -> list[Source[Any, Any, Any]]:
        return list(self._bound_callbacks.keys())

    async def start(self) -> None:
        await self._db.init()
        while True:
            timeout = await self.sync()
            await asyncio.sleep(timeout)

            del_tasks: set[asyncio.Task[Any]] = set()
            for task in self._running_tasks:
                if task.done():
                    exception = task.exception()
                    if exception is not None:
                        logger.exception(__("An error occurred while executing a callback."), exc_info=exception)
                    del_tasks.add(task)

            for task in del_tasks:
                self._running_tasks.remove(task)

    async def sync(self) -> float:
        for source, callbacks in self._bound_callbacks.items():
            if self._timeouts[source.name] > dt.datetime.now():
                continue

            try:
                last: Iterable[HistoryContent] = await source.get_recent(30)
            except SourceDown:
                logger.exception(__("Source {} is down.", source.name), exc_info=True)
                continue
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    __("An error occurred while fetching {}'s recent content.", source.name), exc_info=True
                )
                continue

            new_elements = [
                content for content in last if not await self._db.already_processed(source.name, content.id)
            ]
            not_posted = [
                content for content in new_elements if not await self._db.is_duplicate(content.normalized_name)
            ]
            for content in new_elements:
                await self._db.add(source.name, content.id, content.normalized_name, content in not_posted)

            if timeout := getattr(source, "timeout", None):
                self._timeouts[source.name] = dt.datetime.now() + dt.timedelta(seconds=timeout)
            else:
                self._timeouts[source.name] = dt.datetime.now() + dt.timedelta(seconds=self.default_timeout)

            for callback in callbacks:
                for new in reversed(not_posted):
                    self._running_tasks.append(asyncio.create_task(callback(source, new)))

        return min(until - dt.datetime.now() for until in self._timeouts.values()).total_seconds()

    def sub_to(
        self, *sources: SourceT
    ) -> Callable[[Callback[SourceT, RecentT_co, ReturnT]], Callback[SourceT, RecentT_co, ReturnT]]:
        def decorator(func: Callback[SourceT, RecentT_co, ReturnT]) -> Callback[SourceT, RecentT_co, ReturnT]:
            for source in sources:
                source.client = self._client
                self._bound_callbacks.setdefault(source, []).append(func)
                self._timeouts.setdefault(source.name, dt.datetime.now())
            return func

        return decorator


class Database:
    def __init__(self, path: str):
        self.path = pathlib.Path(path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self):
        self._connection = await aiosqlite.connect(self.path)

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            raise RuntimeError("You must fist connect to the database using `await db.connect()`")
        return self._connection

    @property
    def cursor(self):
        return self.connection.cursor

    async def init(self):
        if self._connection is None:
            await self.connect()

        async with self.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                url TEXT,
                normalized_content TEXT,
                published INTEGER
            )
            """
            await cursor.execute(sql)
        await self.connection.commit()

    async def already_processed(self, source: str, content_id: str) -> bool:
        sql = """SELECT * FROM history WHERE source = ? AND url = ?"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (source, content_id))
            return await cursor.fetchone() is not None

    async def is_duplicate(self, normalized: str) -> bool:
        sql = """SELECT * FROM history WHERE normalized_content = ?"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (normalized,))
            return await cursor.fetchone() is not None

    async def add(self, source: str, content_id: str, normalized: str, published: int) -> None:
        sql = """INSERT INTO history (source, url, normalized_content, published) VALUES (?, ?, ?, ?)"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (source, content_id, normalized, published))
        await self.connection.commit()
