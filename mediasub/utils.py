from itertools import chain, islice
from typing import Generator, Iterable, Sequence, TypeVar

T = TypeVar("T")


def chunker(it: Iterable[T], n: int) -> Generator[Sequence[T], None, None]:
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(it)
    while True:
        chunk_it = islice(it, n)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield tuple(chain((first_el,), chunk_it))
