from collections.abc import Callable

from typing_extensions import TYPE_CHECKING, Any, Coroutine, TypeVar

if TYPE_CHECKING:
    from .source import Identifiable, Source

ET_co = TypeVar("ET_co", bound="Identifiable", covariant=True, default="Identifiable")
ReturnT = TypeVar("ReturnT", default=Any)
SourceT = TypeVar("SourceT", bound="Source")


Coro = Coroutine[Any, Any, ReturnT]

Callback = Callable[[SourceT, ET_co], Coro[ReturnT]]
