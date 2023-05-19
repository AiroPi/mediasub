import asyncio
import logging

from mediasub import MediaSub
from mediasub.models import Chapter, MangaSource

logger = logging.getLogger(__name__)

media_sub = MediaSub("./history.sqlite")


MangaDex: MangaSource  # not implemented, only used as example


@media_sub.sub_to(MangaSource, MangaDex())
async def on_new_chapter(source: MangaSource, chapter: Chapter) -> None:
    print(chapter.manga.name, "#", chapter.number, f"({chapter.name})")

    if source.supports_download:
        pages = await source.get_pages(chapter)
        for page in pages:
            filename, bytes_img = await source.download(page)
            with open(f"page_{page.number}_{filename}", "wb") as f:
                f.write(bytes_img.read())


asyncio.run(media_sub.start())
