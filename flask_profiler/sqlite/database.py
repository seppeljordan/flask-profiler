from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

from flask_profiler import query as q
from flask_profiler.entities import measurement_archive as interface

from .migrations import Migrations
from .select_query import RecordResult

LOGGER = logging.getLogger(__name__)


class Sqlite:
    def __init__(self, sqlite_file: str) -> None:
        self.sqlite_file = sqlite_file
        self.connection = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.create_database()

    def create_database(self) -> None:
        migrations = Migrations(self.connection)
        migrations.run_necessary_migrations()

    def record_measurement(self, measurement: interface.Measurement) -> None:
        LOGGER.debug("Recording measurement %s", measurement)
        query = q.Insert(
            into=q.Identifier("measurements"),
            columns=[
                q.Identifier("route_name"),
                q.Identifier("start_timestamp"),
                q.Identifier("end_timestamp"),
                q.Identifier("method"),
            ],
            rows=[
                [
                    q.Literal(measurement.route_name),
                    q.Literal(measurement.start_timestamp.timestamp()),
                    q.Literal(measurement.end_timestamp.timestamp()),
                    q.Literal(measurement.method),
                ]
            ],
        )
        self.cursor.execute(str(query))
        self.connection.commit()

    def get_records(self) -> RecordResult:
        return RecordResult(
            db=self.cursor,
            mapping=self._row_to_record,
            query=q.Select(
                selector=q.SelectorList(
                    [
                        q.All(),
                        q.Alias(
                            expression=q.BinaryOp(
                                "-",
                                q.Identifier("end_timestamp"),
                                q.Identifier("start_timestamp"),
                            ),
                            name=q.Identifier("elapsed"),
                        ),
                    ]
                ),
                from_clause=q.Identifier("measurements"),
            ),
        )

    def close_connection(self) -> None:
        self.connection.close()

    def _row_to_record(self, row) -> interface.Record:
        return interface.Record(
            id=row["ID"],
            start_timestamp=datetime.fromtimestamp(
                row["start_timestamp"], tz=timezone.utc
            ),
            end_timestamp=datetime.fromtimestamp(row["end_timestamp"], tz=timezone.utc),
            method=row["method"],
            name=row["route_name"],
        )