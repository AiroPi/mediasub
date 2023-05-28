from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..utils import normalize
from .base import HistoryContent, NormalizedObject, Source, SupportsDownload, impact_status


class AnimeSource(Source["Episode", "Anime"]):
    @impact_status
    async def get_episodes(self, anime: Anime) -> Iterable[Episode]:
        return await self._get_episodes(anime)

    @abstractmethod
    async def _get_episodes(self, anime: Anime) -> Iterable[Episode]:
        pass


class AnimeSupportsDownload(SupportsDownload["Episode"]):
    pass


@dataclass
class Anime(NormalizedObject):
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
class Episode(HistoryContent):
    anime: Anime
    name: str
    number: int
    language: str | None
    url: str
    sub_number: int | None = None  # for special episodes

    raw_data: Any = field(repr=False, default=None)

    @property
    def normalized_name(self) -> str:
        return f"{normalize(self.anime.name)}/{self.number}{f'.{self.sub_number}' if self.sub_number else ''}"

    @property
    def display(self) -> str:
        return f"{self.anime.display} - {self.name}"

    @property
    def id(self) -> str:
        return f"{self.url}"
