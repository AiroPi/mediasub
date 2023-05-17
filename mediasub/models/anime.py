from dataclasses import dataclass, field
from typing import Any


@dataclass
class Anime:
    name: str
    language: str | None
    url: str

    raw_data: Any = field(repr=False)


class Episode:
    pass
