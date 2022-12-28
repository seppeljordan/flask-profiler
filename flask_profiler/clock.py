import time
from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    def get_epoch(self) -> float:
        ...

    def utc_now(self) -> datetime:
        ...


class SystemClock:
    def get_epoch(self) -> float:
        return time.time()

    def utc_now(self) -> datetime:
        return datetime.now(tz=timezone.utc)
