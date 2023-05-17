from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from typing import Generic, Iterable, TypeVar

import httpx

from .._logger import BraceMessage as __

_SEARCH = TypeVar("_SEARCH")
_RECENT = TypeVar("_RECENT")
_DL = TypeVar("_DL")

logger = logging.getLogger(__name__)


class Source(ABC, Generic[_RECENT, _SEARCH, _DL]):
    name: str
    _client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            logger.warning(__("No client defined for source {}, so a new one has been created.", self.name))
            self._client = httpx.AsyncClient()
        return self._client

    @client.setter
    def client(self, client: httpx.AsyncClient):
        self._client = client

    @abstractmethod
    async def get_recent(self, limit: int, before: int | None = None) -> Iterable[_RECENT]:
        pass

    @abstractmethod
    async def search(self, query: str) -> Iterable[_SEARCH]:
        pass

    @property
    def supports_download(self) -> bool:
        return self.__class__._download is not Source._download  # pyright: ignore[reportUnknownMemberType]

    async def download(self, target: _DL) -> tuple[str, io.BytesIO]:
        return await self._download(target)

    async def _download(self, target: _DL) -> tuple[str, io.BytesIO]:
        raise NotImplementedError
