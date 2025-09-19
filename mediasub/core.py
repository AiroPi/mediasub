from __future__ import annotations

import asyncio
import datetime as dt
import logging
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Never

import httpx

from ._logger import BraceMessage as __, setup_logger
from .database import Database
from .errors import SourceDown
from .source import Identifiable, PullSource, Source, Status

if TYPE_CHECKING:
    from .types import Callback, ID_co, ReturnT, SourceT

setup_logger("mediasub")
logger = logging.getLogger(__name__)


class MediaSub:
    def __init__(self, db_path: str):
        self._db = Database(db_path)
        self._webclient = httpx.AsyncClient(follow_redirects=True)
        self._timeouts: dict[str, dt.datetime] = {}
        self._bound_callbacks: dict[Source, list[Callback[Any, Any, Any]]] = {}
        self._running_tasks: list[asyncio.Task[Any]] = []

    @property
    def sources(self) -> list[Source]:
        """Returns a list of all the sources recorded using MediaSub.sub_to"""
        return list(self._bound_callbacks.keys())

    async def start(self) -> Never:
        """Starts the main loop.

        This method will never return.
        The loop sync the sources, and wait until the first timeout is reached.
        sync add tasks to self._running_tasks. These tasks are cleaned up by the main loop.
        """
        await self._db.init()

        while True:
            timeout = await self.sync()
            await asyncio.sleep(timeout)

            del_tasks: set[asyncio.Task[Any]] = set()
            for task in self._running_tasks:
                if task.done():
                    exception = task.exception()
                    if exception is not None:
                        logger.exception(
                            __("An error occurred while executing a callback."),
                            exc_info=exception,
                        )
                    del_tasks.add(task)

            for task in del_tasks:
                self._running_tasks.remove(task)

    async def _handle_content(self, src: Source, *contents: Identifiable) -> None:
        """This is the method called by sync and publish to manage the new content.

        This function filter the new content to only keep the ones that have not been processed yet.
        Then it add them to the database, and call the callbacks bound to the source.

        Args:
            src: the source from which the content comes
            *contents: the new content
        """
        callbacks = self._bound_callbacks[src]

        new_elements = [content for content in contents if not await self._db.already_processed(content)]
        for content in reversed(new_elements):
            await self._db.add(content)

            for callback in callbacks:
                self._running_tasks.append(asyncio.create_task(callback(src, content)))

    async def sync(self) -> float:
        """Synchronize the source, getting the last published contents.

        This function iter over all the sources, ignoring the ones that did not reach their timeout.

        Returns:
            The time until the next timeout, in seconds.
        """
        for source in self._bound_callbacks:
            if not isinstance(source, PullSource):
                continue

            if self._timeouts[source.name] > dt.datetime.now():
                continue

            self._timeouts[source.name] = dt.datetime.now() + dt.timedelta(
                seconds=source.timeout or source.default_timeout
            )

            try:
                contents: Iterable[Identifiable] = await source.pull()
            except SourceDown:
                if source.status != Status.DOWN:
                    source.status = Status.DOWN
                    logger.warning(__("Source {} is down.", source.name))
                continue
            except Exception as e:
                source.status = Status.UNKNOWN
                logger.exception(
                    __(
                        "An error occurred while fetching {}'s recent content.",
                        source.name,
                    ),
                    exc_info=e,
                )
                continue
            source.status = Status.UP

            try:
                await self._handle_content(source, *contents)
            except Exception:
                logger.exception(__("Error while handling new content for {}", source.name))

        return min(until - dt.datetime.now() for until in self._timeouts.values()).total_seconds()

    async def publish(self, src: Source, *contents: Identifiable) -> None:
        """Pubsub sources use this method to share the new content they get.

        Args:
            src: the source that get some new content
            *contents: all the new content
        """
        await self._handle_content(src, *contents)

    def sub_to(
        self, *sources: SourceT
    ) -> Callable[[Callback[SourceT, ID_co, ReturnT]], Callback[SourceT, ID_co, ReturnT]]:
        """Use this decorator to bind a callback to some sources.

        Example::

                @mediasub.sub_to(Youtube())
                async def on_video(src: Youtube, video: Video):
                    print(f"New video from {video.channel.name} : {video.title}")
        """

        def decorator(
            func: Callback[SourceT, ID_co, ReturnT],
        ) -> Callback[SourceT, ID_co, ReturnT]:
            for source in sources:
                source.client = self._webclient
                self._bound_callbacks.setdefault(source, []).append(func)
                self._timeouts.setdefault(source.name, dt.datetime.now())
            return func

        return decorator
