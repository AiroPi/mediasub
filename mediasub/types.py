from collections.abc import Callable

from typing_extensions import TYPE_CHECKING, Any, Coroutine, TypeVar

if TYPE_CHECKING:
    from .models.base import HistoryContent, NormalizedObject, Source

SearchT_co = TypeVar("SearchT_co", bound="NormalizedObject", covariant=True, default="NormalizedObject")
RecentT_co = TypeVar("RecentT_co", bound="HistoryContent", covariant=True, default="HistoryContent")
DLT = TypeVar("DLT", default=Any)
ReturnT = TypeVar("ReturnT", default=Any)
SourceT = TypeVar("SourceT", bound="Source")


Coro = Coroutine[Any, Any, ReturnT]

Callback = Callable[[SourceT, RecentT_co], Coro[ReturnT]]
