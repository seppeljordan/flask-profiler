from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    def utc_now(self) -> datetime:
        ...


class SystemClock:
    def utc_now(self) -> datetime:
        return datetime.now(tz=timezone.utc)
