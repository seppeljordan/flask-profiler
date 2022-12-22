from __future__ import annotations

import itertools
from pathlib import Path
from sqlite3 import Cursor
from typing import Iterator


class Migration:
    def __init__(self, sql_code: str) -> None:
        self.sql_code = sql_code

    @classmethod
    def from_filename(cls, filename: str) -> Migration:
        with open(Path(__file__).parent / f"{filename}.sql") as f:
            sql_code = f.read()
        return cls(sql_code)

    def run(self, cursor: Cursor) -> None:
        cursor.executescript(self.sql_code)


class Migrations:
    def __init__(self) -> None:
        self.migration_files = ["migration_1"]

    def get_relevant_versions(self, version: int) -> Iterator[Migration]:
        yield from map(
            Migration.from_filename,
            itertools.islice(self.migration_files, version, None),
        )

    def latest_version(self) -> int:
        return len(self.migration_files)
