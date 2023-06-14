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
from .source import Identifiable, PollSource, Source, Status

if TYPE_CHECKING:
    from .types import Callback, ET_co, ReturnT, SourceT

setup_logger("mediasub")
logger = logging.getLogger(__name__)


class MediaSub:
    def __init__(self, db_path: str):
        self._db = Database(db_path)
        self._client = httpx.AsyncClient(follow_redirects=True)
        self._timeouts: dict[str, dt.datetime] = {}
        self._bound_callbacks: dict[Source, list[Callback[Any, Any, Any]]] = {}
        self._running_tasks: list[asyncio.Task[Any]] = []

    @property
    def sources(self) -> list[Source]:
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

    async def _manage_content(self, src: Source, *contents: Identifiable) -> None:
        callbacks = self._bound_callbacks[src]

        new_elements = [content for content in contents if not await self._db.already_processed(content)]
        for content in reversed(new_elements):
            await self._db.add(content)

            for callback in callbacks:
                self._running_tasks.append(asyncio.create_task(callback(src, content)))

    async def sync(self) -> float:
        for source in self._bound_callbacks.items():
            if not isinstance(source, PollSource):
                continue

            if self._timeouts[source.name] > dt.datetime.now():
                continue

            try:
                contents: Iterable[Identifiable] = await source.poll()  # TODO(airo.pi_): provide context
            except SourceDown:
                if source.status != Status.DOWN:
                    source.status = Status.DOWN
                    logger.warning(__("Source {} is down.", source.name))
                continue
            except Exception:  # pylint: disable=broad-except
                source.status = Status.UNKNOWN
                logger.exception(
                    __("An error occurred while fetching {}'s recent content.", source.name), exc_info=True
                )
                continue
            source.status = Status.UP

            await self._manage_content(source, *contents)
            self._timeouts[source.name] = dt.datetime.now() + dt.timedelta(seconds=source.timeout)

        return min(until - dt.datetime.now() for until in self._timeouts.values()).total_seconds()

    async def publish(self, src: Source, *contents: Identifiable) -> None:
        """Pubsub sources use this method to share the new content they get.

        Args:
            src: the source that get some new content
            *contents: all the new content
        """
        await self._manage_content(src, *contents)

    def sub_to(
        self, *sources: SourceT
    ) -> Callable[[Callback[SourceT, ET_co, ReturnT]], Callback[SourceT, ET_co, ReturnT]]:
        def decorator(func: Callback[SourceT, ET_co, ReturnT]) -> Callback[SourceT, ET_co, ReturnT]:
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
                identifier TEXT
            )
            """
            await cursor.execute(sql)
        await self.connection.commit()

    async def already_processed(self, content: Identifiable) -> bool:
        sql = """SELECT * FROM history WHERE identifier = ?"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (content.db_identifier,))
            return await cursor.fetchone() is not None

    async def add(self, content: Identifiable) -> None:
        sql = """INSERT INTO history (identifier) VALUES (?)"""
        async with self.cursor() as cursor:
            await cursor.execute(sql, (content.db_identifier,))
        await self.connection.commit()
