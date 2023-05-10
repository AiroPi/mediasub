import datetime
import time
from typing import Any

def parse(
    url_file_stream_or_string: Any,
    etag: str | None = None,
    modified: str | tuple[time.struct_time, ...] | datetime.datetime | None = None,
    agent: str | None = None,
    referrer: Any | None = None,
    handlers: Any | None = None,
    request_headers: dict[str, str] | None = None,
    response_headers: dict[str, str] | None = None,
    resolve_relative_uris: bool | None = None,
    sanitize_html: bool | None = None,
) -> Any:
    pass
