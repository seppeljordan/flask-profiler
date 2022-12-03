import time
from typing import Protocol


class Clock(Protocol):
    def get_epoch(self) -> float:
        ...


class SystemClock:
    def get_epoch(self) -> float:
        return time.time()
