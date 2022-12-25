from __future__ import annotations

import itertools
import logging
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Iterator

from flask_profiler import query as q

LOGGER = logging.getLogger(__name__)


class Migration:
    def __init__(self, sql_code: str) -> None:
        self.sql_code = sql_code

    @classmethod
    def from_filename(cls, filename: str) -> Migration:
        with open(Path(__file__).parent / f"{filename}.sql") as f:
            sql_code = f.read()
        return cls(sql_code)

    def run(self, cursor: Cursor) -> None:
        LOGGER.debug("Run migration %s", self.sql_code)
        cursor.executescript(self.sql_code)


class Migrations:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.migration_files = ["migration_1"]

    def run_necessary_migrations(self) -> None:
        cursor = self.connection.cursor()
        for migration in self.get_relevant_versions(cursor):
            migration.run(cursor)

    def get_relevant_versions(self, cursor: Cursor) -> Iterator[Migration]:
        version = self.get_current_version(cursor)
        yield from map(
            Migration.from_filename,
            itertools.islice(self.migration_files, version, None),
        )

    def get_current_version(self, cursor: Cursor) -> int:
        return cursor.execute(
            q.Pragma(
                name="user_version",
            ).as_statement()
        ).fetchone()[0]
