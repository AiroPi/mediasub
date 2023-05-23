import re
from itertools import chain, islice
from typing import Generator, Iterable, Sequence, TypeVar

from unidecode import unidecode

T = TypeVar("T")


def chunker(iterable: Iterable[T], number: int) -> Generator[Sequence[T], None, None]:
    if number < 1:
        raise ValueError("n must be at least one")
    iterable = iter(iterable)
    while True:
        chunk_it = islice(iterable, number)
        try:
            first_el = next(chunk_it)
        except StopIteration:
            return
        yield tuple(chain((first_el,), chunk_it))


def normalize(string: str) -> str:
    string = unidecode(string).casefold()
    string = string.replace(" ", "_").replace("-", "_")
    string = re.sub(r"([^\w])*", "", string)
    return string
