from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..base import Source
from ..utils import normalize


class AnimeSource(Source["Episode"]):
    @abstractmethod
    async def get_episodes(self, anime: Anime) -> Iterable[Episode]:
        pass


@dataclass
class Anime:
    name: str
    url: str

    raw_data: Any = field(repr=False, default=None)


@dataclass
class Episode:
    anime: Anime
    name: str
    number: int
    language: str | None
    url: str
    sub_number: int | None = None  # for special episodes

    raw_data: Any = field(repr=False, default=None)

    def __post_init__(self):
        self.db_identifier = (
            f"{normalize(self.anime.name)}/{self.number}{f'.{self.sub_number}' if self.sub_number else ''}"
        )
