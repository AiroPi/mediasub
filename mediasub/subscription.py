from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging
import pathlib
from typing import Any, Callable, Coroutine, Type, TypeVar

import httpx

from ._logger import setup_logger
from .models.base import Source

setup_logger()
logger = logging.getLogger(__name__)


_RT = TypeVar("_RT")
R = TypeVar("R")
S = TypeVar("S", bound=Source[Any, Any, Any])
Coro = Coroutine[Any, Any, R]

Callback = Callable[[S, _RT], Coro[R]]


class MediaSub:
    default_timeout = 300  # in seconds

    def __init__(self, db_path: str = "history.json"):
        self.db_path = pathlib.Path(db_path)
        self._client = httpx.AsyncClient()
        self.timeouts: dict[str, dt.datetime] = {}
        self.bound_callbacks: dict[Source[Any, Any, Any], list[Callback[Any, Any, Any]]] = {}
        self.running_tasks: list[asyncio.Task[Any]] = []

        self._history = self.load_history()

    async def start(self) -> None:
        while True:
            timeout = await self.sync()
            await asyncio.sleep(timeout)

            self.running_tasks = [task for task in self.running_tasks if not task.done()]

    async def sync(self) -> float:
        for source, callbacks in self.bound_callbacks.items():
            if self.timeouts[source.name] > dt.datetime.now():
                continue

            last = await source.get_recent(10)
            news = [content for content in last if content.id not in self._history]
            self._history.extend(content.id for content in news)
            self.dump_history()

            if timeout := getattr(source, "timeout", None):
                self.timeouts[source.name] = dt.datetime.now() + dt.timedelta(seconds=timeout)
            else:
                self.timeouts[source.name] = dt.datetime.now() + dt.timedelta(seconds=self.default_timeout)

            for callback in callbacks:
                for new in news:
                    self.running_tasks.append(asyncio.create_task(callback(source, new)))

        return min(until - dt.datetime.now() for until in self.timeouts.values()).total_seconds()

    def sub_to(
        self, cls: Type[S], *sources: Source[_RT, Any, Any]
    ) -> Callable[[Callback[S, _RT, R]], Callback[S, _RT, R]]:
        for source in sources:
            if not isinstance(source, cls):
                raise ValueError(f"Source {source} is not an instance of {cls}")

        def decorator(func: Callback[S, _RT, R]) -> Callback[S, _RT, R]:
            for source in sources:
                source.client = self._client
                self.bound_callbacks.setdefault(source, []).append(func)
                self.timeouts.setdefault(source.name, dt.datetime.now())
            return func

        return decorator

    def load_history(self) -> list[str]:
        if not self.db_path.exists():
            with self.db_path.open("w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        with self.db_path.open("r") as f:
            return json.load(f)

    def dump_history(self) -> None:
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(self._history, f)
