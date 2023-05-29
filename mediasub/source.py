from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Generic, Iterable, ParamSpec, Protocol, TypeVar, runtime_checkable

import httpx

from ._logger import BraceMessage as __
from .types import ET_co

if TYPE_CHECKING:
    R = TypeVar("R")
    P = ParamSpec("P")
    S = TypeVar("S", bound="Source")


logger = logging.getLogger(__name__)


class Status(Enum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "WARNING"


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

    @abstractmethod
    async def get_recent(self, limit: int = 25) -> Iterable[ET_co]:
        ...


@runtime_checkable
class Identifiable(Protocol):
    """
    Avoid duplication by implementing a unique identification name for the content.
    This name should be the same for the same content, no matter the source.
    """

    @property
    def db_identifier(self) -> str:
        ...
