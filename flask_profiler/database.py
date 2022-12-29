from typing import Protocol


class Database(Protocol):
    def close_connection(self) -> None:
        ...
