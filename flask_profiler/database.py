from typing import Protocol


class Database(Protocol):
    def close_connection(self) -> None:
        ...

    def create_database(self) -> None:
        ...
