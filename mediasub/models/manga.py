from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..base import Source
from ..utils import normalize


class MangaSource(Source["Chapter"]):
    @abstractmethod
    async def get_pages(self, chapter: Chapter) -> Iterable[Page]:
        pass


@dataclass
class Manga:
    name: str
    url: str

    raw_data: Any = field(repr=False, default=None)


@dataclass
class Chapter:
    manga: Manga
    name: str
    number: int
    language: str | None
    url: str
    sub_number: int | None = None  # for special chapters

    raw_data: Any = field(repr=False, default=None)

    def __post_init__(self):
        self.db_identifier = (
            f"{normalize(self.manga.name)}/{self.number}{f'.{self.sub_number}' if self.sub_number else ''}"
        )


@dataclass
class Page:
    chapter: Chapter
    number: int
    url: str

    raw_data: Any = field(repr=False, default=None)
