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
    """Normalize a string, useful for making identifiers.

    This method will:
        - lowercase the string
        - remove special characters
        - replace kanji etc.. with their latin equivalent
        - replace the spaces and the "-" with an underscore

    Example:
        `OnePiece`, `one-piece` or `one piece` become `one_piece`.

    Args:
        string: the string you want to normalize.

    Returns:
        the normalized string.
    """
    string = unidecode(string).casefold()
    string = string.replace(" ", "_").replace("-", "_")
    string = re.sub(r"([^\w])*", "", string)
    return string
