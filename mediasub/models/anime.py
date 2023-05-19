from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..utils import normalize
from .base import HistoryContent, Source, impact_status


class AnimeSource(Source["Episode", "Anime", "Episode"]):
    @impact_status
    async def get_episodes(self, anime: Anime) -> Iterable[Episode]:
        return await self._get_episodes(anime)

    @abstractmethod
    async def _get_episodes(self, anime: Anime) -> Iterable[Episode]:
        pass


@dataclass
class Anime:
    name: str
    url: str

    raw_data: Any = field(repr=False, default=None)


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
    def id(self) -> str:
        return f"{self.url}"
