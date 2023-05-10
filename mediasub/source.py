from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterable, Iterable, TypeVar

import httpx

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .content import Content

T = TypeVar("T")


class Source(ABC):
    name: str
    _client: httpx.AsyncClient

    def set_client(self, client: httpx.AsyncClient) -> None:
        self._client = client

    @abstractmethod
    async def get_last_content(self, limit: int, before: int | None = None) -> Iterable[Content]:
        pass

    @property
    def downloadable(self) -> bool:
        return self.__class__._download is not Source._download

    @property
    def fragmented_downloadable(self) -> bool:
        return self.__class__._fragmented_download is not Source._fragmented_download

    def fragmented_download(self, content: Content) -> AsyncIterable[Any]:
        if not isinstance(content.source, type(self)):
            raise ValueError("Content source does not match with this source.")
        return self._fragmented_download(content)

    def _fragmented_download(self, content: Content) -> AsyncIterable[Any]:
        raise NotImplementedError

    async def download(self, content: Content) -> Any:
        if not isinstance(content.source, type(self)):
            raise ValueError("Content source does not match with this source.")
        return self._download(content)

    async def _download(self, content: Content) -> Any:
        raise NotImplementedError
