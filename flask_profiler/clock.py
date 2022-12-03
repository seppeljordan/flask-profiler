from typing import Protocol


class Clock(Protocol):
    def get_epoch(self) -> float:
        ...
