from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Generic,
    NamedTuple,
    ParamSpec,
    Protocol,
    TypeVar,
)

import httpx

from ._logger import BraceMessage as __
from .types import ID_co

if TYPE_CHECKING:
    from mediasub.core import MediaSub

    R = TypeVar("R")
    P = ParamSpec("P")
    S = TypeVar("S", bound="Source")


logger = logging.getLogger(__name__)


class LastPullContext(NamedTuple):
    date: datetime
    identifier: str


class Status(Enum):
    """Different status a source can have.

    Attributes:
        UP: the source is UP
        DOWN: SourceDown exception raised while pulling new contents
        UNKNOWN: there is currently no informations about the status
        WARNING: an exception has been raised while pulling, other than SourceDown
    """

    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"
    WARNING = "WARNING"


class Source(ABC, Generic[ID_co]):
    """The base class for any source you want to implement.

    All sources you want to implement must inherit from PullSource or PubsubSource, that inherit from Source.
    You must define a name, and an url for every source you create.

    Attributes:
        shared_client: False if the class has its own http client.
        status: the source current status.

    Example::

        class GoogleNewsRSS(PullSource[Article]):
            name = "GoogleNews"
            url = "https://example.com/feed"
            ...

    """

    def __init__(self, shared_client: bool = False):
        """Inits Source.

        Note:
            By using `MediaSub.subto(AnySource)`, the module will define a shared client that will be used by all
            the sources. You can set `shared_client` to `False` if you want to class to have it's own http client.
            If `shared_client` is `True` but for any reason you use the source without the MediaSub.subto decorator,
            a warning message will be logged telling you that a http client has been created.

        Args:
            shared_client: tell is the Source should have it's own http client or the shared one.
        """
        self.shared_client = shared_client
        self.status: Status = Status.UNKNOWN
        self._client: httpx.AsyncClient | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the source"""

    # @property
    # @abstractmethod
    # def url(self) -> str:
    #     """The url of the source."""

    @property
    def client(self) -> httpx.AsyncClient:
        """A httpx.AsyncClient you can use to make your requests"""
        if self._client is None:
            if not self.shared_client:
                logger.warning(
                    __(
                        "No client defined for source {}, so a new one has been created.",
                        self.name,
                    )
                )
            self._client = httpx.AsyncClient(follow_redirects=True)
        return self._client

    @client.setter
    def client(self, client: httpx.AsyncClient):
        self._client = client


class PullSource(Source):
    """A source working by pulling the content.

    If your source just provide a list of contents (or if your scrap a page), you should use PullSource as a base.
    The pull method will be called periodically by the core of the module.
    """

    def __init__(self, shared_client: bool = False, timeout: int = 300):
        """Inits PullSource.

        Args:
            shared_client: if False, an http client is created only for this Source
            timeout: the delay in seconds between 2 pulls. Defaults to 300.
        """
        super().__init__(shared_client)
        self.timeout = timeout

    @abstractmethod
    async def pull(self, last_pull_ctx: LastPullContext | None = None) -> Iterable[ID_co]:
        """A method called periodically by the core to check for new content.


        Args:
            last_pull_ctx: some informations about the last pull, can be used to optimize the pull process.

        Returns:
            An iterable of "new" contents, or last contents.
            This function *can* returns already processed contents if their ID is still the same.
            The core will ignore them.
        """


class PubsubSource(Source):
    """A source working by being subscribed to a content flux.

    If your source is "averted" by the provider that there is new content, you should use PubsubSource as a base.
    Your PubsubSource will then needs to call the MediaSub.publish method, that will then call the corresponding
    callbacks.

    Example::

        class YoutubeVideo(PubsubSource[Video]):
            @app.get("/youtube-pubsub")
            async def on_video(self, raw_data: Any):
                content: Video = transform_to_video(raw_data)
                await self.publish(content)
    """

    _bound: MediaSub

    async def publish(self, *contents: Identifiable) -> None:
        """Use this method to call the callbacks when there is new content available.

        Args:
            *contents: the new content(s) available.
        """
        await self._bound.publish(self, *contents)

    def bind(self, bound: MediaSub):
        """
        Allow the core to bound a source with a MediaSub instance.
        This should not be called otherwise.
        """
        self._bound: MediaSub = bound


class Identifiable(Protocol):
    """A protocol describing the content that sources provide.

    Avoid duplication by implementing a unique identification name for the content.
    This name should be the same for the same content, no matter the source.

    For example, if a source A has a content named "OnePiece", and a source B has the same new content but named
    "one-piece", they should have the same identifier. This is only important if you have multiple sources for the same
    type of content. You can use the helper function `utils.normalize`.

    This identifier is used by the core to avoid sending the same content twice.
    """

    @property
    def id(self) -> str:
        """The unique ID of a content."""
        ...
