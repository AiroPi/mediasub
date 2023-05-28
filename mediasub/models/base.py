from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Callable, Concatenate, Generic, Iterable, ParamSpec, TypeVar

import httpx

from .._logger import BraceMessage as __
from ..errors import SourceDown
from ..types import DLT, Coro, RecentT_co, SearchT_co

if TYPE_CHECKING:
    R = TypeVar("R")
    P = ParamSpec("P")
    S = TypeVar("S", bound="Source")


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


class Source(ABC, Generic[RecentT_co, SearchT_co]):
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
    async def get_recent(self, limit: int, before: int | None = None) -> Iterable[RecentT_co]:
        return await self._get_recent(limit, before)

    @abstractmethod
    async def _get_recent(self, limit: int, before: int | None = None) -> Iterable[RecentT_co]:
        pass

    @impact_status
    async def search(self, query: str) -> Iterable[SearchT_co]:
        return await self._search(query)

    @abstractmethod
    async def _search(self, query: str) -> Iterable[SearchT_co]:
        pass

    @impact_status
    async def all(self) -> Iterable[SearchT_co]:
        return await self._all()

    @abstractmethod
    async def _all(self) -> Iterable[SearchT_co]:
        pass


class SupportsDownload(ABC, Generic[DLT]):
    @abstractmethod
    async def download(self, target: DLT) -> tuple[str, io.BytesIO]:
        pass


class NormalizedObject(ABC):
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

    @property
    @abstractmethod
    def display(self) -> str:
        """
        Return a string that can be displayed to the user.
        """


class HistoryContent(NormalizedObject):
    @property
    @abstractmethod
    def id(self) -> str:
        pass
