from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, AsyncIterable

if TYPE_CHECKING:
    from .source import Source


logger = logging.getLogger(__name__)


class ContentType(Enum):
    MANGA_SCAN = auto()
    MANGA_EPISODE = auto()
    MOVIE = auto()
    BOOK = auto()


@dataclass
class Content:
    source: Source
    content_type: ContentType
    raw_data: Any = field(repr=False)
    series_name: str
    series_id: str
    name: str
    language: str | None
    chapter: int | None
    url: str

    @property
    def id(self) -> str:
        return f"{self.source.name}:{self.content_type.name}:{self.series_id}:{self.name}"

    @property
    def downloadable(self) -> bool:
        return self.source.downloadable

    @property
    def fragmented_downloadable(self) -> bool:
        return self.source.fragmented_downloadable

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Content):
            return False
        return self.id == __value.id

    def fragmented_download(self) -> AsyncIterable[tuple[str, io.BytesIO]]:
        return self.source.fragmented_download(self)

    async def download(self) -> tuple[str, io.BytesIO]:
        return await self.source.download(self)
