class SourceDown(Exception):
    """Raised when a website is not reachable, ie it is down."""

    def __init__(self, trigger: Exception | None = None) -> None:
        self.trigger = trigger
