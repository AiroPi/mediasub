from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Concatenate, Generic, Iterable, ParamSpec, TypeVar

import httpx

from .._logger import BraceMessage as __
from ..errors import SourceDown
from ..types import T_DL, T_RECENT, T_SEARCH, Coro

R = TypeVar("R")
P = ParamSpec("P")
S = TypeVar("S", bound="Source[Any, Any, Any]")


logger = logging.getLogger(__name__)


class Status(Enum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "WARNING"


def impact_status(func: Callable[Concatenate[S, P], Coro[R]]) -> Callable[Concatenate[S, P], Coro[R]]:
    async def inner(source: S, *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            res = await func(source, *args, **kwargs)
        except SourceDown:
            source.status = Status.DOWN
            raise
        except:
            source.status = Status.UP
            raise
        return res

    return inner


class Source(ABC, Generic[T_RECENT, T_SEARCH, T_DL]):
    name: str

    def __init__(self, without_subscription: bool = False):
        self.without_subscription = without_subscription
        self.status: Status = Status.UNKNOWN
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            if not self.without_subscription:
                logger.warning(__("No client defined for source {}, so a new one has been created.", self.name))
            self._client = httpx.AsyncClient()
        return self._client

    @client.setter
    def client(self, client: httpx.AsyncClient):
        self._client = client

    @impact_status
    async def get_recent(self, limit: int, before: int | None = None) -> Iterable[T_RECENT]:
        return await self._get_recent(limit, before)

    @abstractmethod
    async def _get_recent(self, limit: int, before: int | None = None) -> Iterable[T_RECENT]:
        pass

    @impact_status
    async def search(self, query: str) -> Iterable[T_SEARCH]:
        return await self._search(query)

    @abstractmethod
    async def _search(self, query: str) -> Iterable[T_SEARCH]:
        pass

    @property
    def supports_download(self) -> bool:
        return self.__class__._download is not Source._download  # pyright: ignore[reportUnknownMemberType]

    async def download(self, target: T_DL) -> tuple[str, io.BytesIO]:
        return await self._download(target)

    async def _download(self, target: T_DL) -> tuple[str, io.BytesIO]:
        raise NotImplementedError


class HistoryContent(ABC):
    @property
    @abstractmethod
    def normalized_name(self) -> str:
        """
        Return a simplified name for the content. It should respect the following rules:
         1. string is lowercased
         2. accents are removed
         3. kanjis etc.. are replaced by their latin equivalent
         4. spaces and - are replaced by underscores
         5. special characters are removed (except for numbers and underscores)

        These rules could change depending on the source.
        For example, for a manga chapter, it could be formatted as:
        "manga_name/xxx" where xxx is the chapter number.
        """
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        pass
