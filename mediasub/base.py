from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Generic,
    Iterable,
    ParamSpec,
    Protocol,
    TypeVar,
    runtime_checkable,
)

import httpx

from ._logger import BraceMessage as __
from .errors import SourceDown
from .types import Coro, ET_co

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


class Source(ABC, Generic[ET_co]):
    name: str
    url: str

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
    async def get_recent(self, limit: int = 25) -> Iterable[ET_co]:
        return await self._get_recent(limit)

    @abstractmethod
    async def _get_recent(self, limit: int) -> Iterable[ET_co]:
        pass

    @property
    def supports_download(self) -> bool:
        return isinstance(self, SupportsDownload)


@runtime_checkable
class Identifiable(Protocol):
    """
    Avoid duplication by implementing a unique identification name for the content.
    This name should be the same for the same content, no matter the source.
    """

    @property
    def db_identifier(self) -> str:
        ...


@runtime_checkable
class SupportsDownload(Protocol):
    async def download(self, target: Any) -> tuple[str, io.BytesIO]:
        ...
