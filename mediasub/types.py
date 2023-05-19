from collections.abc import Callable

from typing_extensions import TYPE_CHECKING, Any, Coroutine, TypeVar

if TYPE_CHECKING:
    from .models.base import HistoryContent, NormalizedObject, Source

T_SEARCH = TypeVar("T_SEARCH", bound="NormalizedObject", covariant=True, default="NormalizedObject")
T_RECENT = TypeVar("T_RECENT", bound="HistoryContent", covariant=True, default="HistoryContent")
T_DL = TypeVar("T_DL", default=Any)
T_RETURN = TypeVar("T_RETURN", default=Any)
T_SOURCE = TypeVar("T_SOURCE", bound="Source")


Coro = Coroutine[Any, Any, T_RETURN]

Callback = Callable[[T_SOURCE, T_RECENT], Coro[T_RETURN]]
