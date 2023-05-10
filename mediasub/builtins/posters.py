from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import httpx

from .._logger import BraceMessage as __

if TYPE_CHECKING:
    from ..content import Content

logger = logging.getLogger(__name__)


class Poster(ABC):
    @abstractmethod
    async def post(self, content: Content) -> None:
        pass


class ForumWebhook(Poster):
    def __init__(self, webhook: str) -> None:
        self._client = httpx.AsyncClient()
        self._webhook = webhook

    async def post(self, content: Content) -> None:
        wh_data = {
            "thread_name": f"{content.series_name} - chapter {content.chapter}",
            "embeds": [
                {
                    "title": "New chapter",
                    "description": f"**{content.series_name}** - chapter {content.chapter}",
                    "url": content.url,
                    "fields": [
                        {
                            "name": "Language",
                            "value": content.language or "unknown (probably french)",
                            "inline": True,
                        },
                        {"name": "Chapter name", "value": content.name, "inline": True},
                    ],
                }
            ],
        }
        logger.info(__("Sending webhook for {}, chapter {}", content.series_name, content.chapter))
        response = await self._client.post(json=wh_data, url=self._webhook, params={"wait": True})
        thread_id = response.json()["channel_id"]

        async def send(chunk: list[tuple[str, io.BytesIO]]) -> None:
            if len(chunk) == 0:
                return
            _chunk = [(img[0], (f"SPOILER_chapter{content.chapter}-{img[0]}", img[1])) for img in chunk]
            await self._client.post(self._webhook, files=_chunk, params={"thread_id": thread_id})

        try:
            acc: list[tuple[str, io.BytesIO]] = []
            async for page in content.fragmented_download():
                acc.append(page)
                if len(acc) == 10:
                    await send(acc)
                    acc = []
            await send(acc)
        except NotImplementedError:
            pass


class MultipleWebhooks(Poster):
    def __init__(self, webhooks: dict[str, str]) -> None:
        self._client = httpx.AsyncClient()
        self._webhooks = webhooks

    async def post(self, content: Content) -> None:
        wh_data = {
            "embeds": [
                {
                    "title": "New chapter",
                    "description": f"**{content.series_name}** - chapter {content.chapter}",
                    "url": content.url,
                    "fields": [
                        {
                            "name": "Language",
                            "value": content.language or "unknown (probably french)",
                            "inline": True,
                        },
                        {"name": "Chapter name", "value": content.name, "inline": True},
                    ],
                }
            ]
        }
        logger.info(__("Sending webhook for {}, chapter {}", content.series_name, content.chapter))
        webhook_url = self._webhooks.get(content.series_name, self._webhooks["global"])
        await self._client.post(json=wh_data, url=webhook_url)

        async def send(chunk: list[tuple[str, io.BytesIO]]) -> None:
            if len(chunk) == 0:
                return
            _chunk = [(img[0], (f"SPOILER_chapter{content.chapter}-{img[0]}", img[1])) for img in chunk]
            await self._client.post(webhook_url, files=_chunk)

        try:
            acc: list[tuple[str, io.BytesIO]] = []
            async for page in content.fragmented_download():
                acc.append(page)
                if len(acc) == 10:
                    await send(acc)
                    acc = []
            await send(acc)
        except NotImplementedError:
            pass
