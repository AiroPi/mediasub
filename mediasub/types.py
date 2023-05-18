from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeVar

if TYPE_CHECKING:
    from .models.base import HistoryContent, Source

T_SEARCH = TypeVar("T_SEARCH")
T_RECENT = TypeVar("T_RECENT", bound="HistoryContent")
T_DL = TypeVar("T_DL")
T_RETURN = TypeVar("T_RETURN")
T_SOURCE = TypeVar("T_SOURCE", bound="Source[Any, Any, Any]")


Coro = Coroutine[Any, Any, T_RETURN]

Callback = Callable[[T_SOURCE, T_RECENT], Coro[T_RETURN]]
