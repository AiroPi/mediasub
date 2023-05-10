from __future__ import annotations

import io
import json
import logging
import re
from typing import TYPE_CHECKING, Any, AsyncIterable, Iterable, TypedDict

import feedparser
from bs4 import BeautifulSoup

from .._logger import BraceMessage as __
from ..content import Content, ContentType
from ..source import Source

if TYPE_CHECKING:
    from .._types import FilePage


logger = logging.getLogger(__name__)


class RawPage(TypedDict):
    page_image: str
    page_slug: int
    external: int


class ScanVFDotNet(Source):
    name = "www.scan-vf.net"
    supports_download = True

    _base_url = "https://www.scan-vf.net/"
    _rss_url = _base_url + "feed"
    _images_url = _base_url + "uploads/manga/"

    _script_extract = re.compile(r"var pages = (\[.+\])", re.MULTILINE)
    _link_scrap = re.compile(r"https://www\.scan-vf\.net/(?P<manga_name>[\w\-.]+)/(?P<chapter>[\w\-.]+)")
    _title_scrap = re.compile(r"(?P<manga_name>[^#]+) #(?P<chapter>\d+)")

    def _get_chapter_from_rss_item(self, item: Any) -> Content:
        logger.info(__("Extracting infos from : {}", item.link))

        # for user-friendly informations
        clean_match = self._title_scrap.match(item.title)
        # for url-friendly informations
        raw_match = self._link_scrap.search(item.link)

        if not clean_match:
            raise ValueError(__("Error when reading the title : {}", item.title))
        if not raw_match:
            raise ValueError(__("Error when reading the content : {}", item.content))
        clean_result = clean_match.groupdict()
        raw_result = raw_match.groupdict()

        return Content(
            self,
            ContentType.MANGA_SCAN,
            raw_result,
            series_name=clean_result["manga_name"],
            series_id=clean_result["manga_name"],
            name=item.summary,
            language=item.content[0].language,
            chapter=int(clean_result["chapter"]),
            url=item.link,
        )

    async def get_last_content(self, limit: int, before: int | None = None) -> Iterable[Content]:
        if before is None:
            before = 0
        feed: Any = feedparser.parse(self._rss_url)

        return (self._get_chapter_from_rss_item(item) for item in feed.entries[before : limit + before])

    async def _get_raw_pages(self, chapter: Content) -> Iterable[RawPage]:
        soup = BeautifulSoup((await self._client.get(chapter.url)).text, features="html.parser")
        script = soup.select_one("body > div.container-fluid > script")

        if not script:
            logger.error(__("Error when looking for the script tag. URL: {}", chapter.url))
            raise ValueError

        match = self._script_extract.search(script.text)
        if not match:
            logger.error(__("Error when looking for the script content. URL: {}", chapter.url))
            raise ValueError

        return json.loads(match.group(1))

    async def _fragmented_download(self, content: Content) -> AsyncIterable[FilePage]:
        for page in await self._get_raw_pages(content):
            page_url = (
                f"{self._images_url}{content.raw_data['manga_name']}/"
                f"chapters/{content.raw_data['chapter']}/{page['page_image']}"
            )
            result = await self._client.get(page_url)

            yield f"{page['page_image']}", io.BytesIO(result.content)
