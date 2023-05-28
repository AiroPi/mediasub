from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..utils import normalize
from .base import HistoryContent, NormalizedObject, Source, SupportsDownload, impact_status


class MangaSource(Source["Chapter", "Manga"]):
    @impact_status
    async def get_pages(self, chapter: Chapter) -> Iterable[Page]:
        return await self._get_pages(chapter)

    @abstractmethod
    async def _get_pages(self, chapter: Chapter) -> Iterable[Page]:
        pass

    @impact_status
    async def get_chapters(self, manga: Manga) -> Iterable[Chapter]:
        return await self._get_chapters(manga)

    @abstractmethod
    async def _get_chapters(self, manga: Manga) -> Iterable[Chapter]:
        pass


@dataclass
class Manga(NormalizedObject):
    name: str
    url: str

    raw_data: Any = field(repr=False, default=None)

    @property
    def normalized_name(self) -> str:
        return normalize(self.name)

    @property
    def display(self) -> str:
        return self.name


@dataclass
class Chapter(HistoryContent):
    manga: Manga
    name: str
    number: int
    language: str | None
    url: str
    sub_number: int | None = None  # for special chapters

    raw_data: Any = field(repr=False, default=None)

    @property
    def normalized_name(self) -> str:
        return f"{self.manga.normalized_name}/{self.number}{f'.{self.sub_number}' if self.sub_number else ''}"

    @property
    def display(self) -> str:
        return f"{self.manga.display}{self.name}"

    @property
    def id(self) -> str:
        return f"{self.url}"


class MangaSupportsDownload(SupportsDownload["Page"]):
    pass


@dataclass
class Page:
    chapter: Chapter
    number: int
    url: str

    raw_data: Any = field(repr=False, default=None)
