import asyncio
import pathlib

from mediasub import Content, MediaSub
from mediasub.builtins.sources import ScanVFDotNet
from mediasub.content import ContentType

media_sub = MediaSub("./history.json")


# By using this decorator, the "new_content" function will now be called when there is new content.
@media_sub.sub_to(ScanVFDotNet())
async def new_content(contents: list[Content]) -> None:
    # "contents" is the list of all the new content published (because lists are checked every x time)
    for content in contents:
        # you can download some contents if available
        if content.downloadable:
            dl = await content.download()
            with open(dl[0], "wb") as f:
                f.write(dl[1].read())

        # MANGA_SCAN content can often be downloaded page by page
        elif content.fragmented_downloadable and content.content_type == ContentType.MANGA_SCAN:
            path = pathlib.Path(content.name)
            path.mkdir(exist_ok=True)

            async for page in content.fragmented_download():
                fragment_path = path / page[0]
                with fragment_path.open("rb") as f:
                    f.write(page[1].read())


# In fact, download methods depend on the source used. They can be defined or not.
# Because here we know that ScanVFDotNet implement the fragmented_downloadable method by returning the scan page by page
# we could use the method directly without any check.
# fragmented_downloadable & downloadable can be used if you use multiple source for the same callback.


asyncio.run(media_sub.start())
