from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from sqlite3 import Cursor
from typing import Any, Callable, Generic, Iterator, TypeVar, cast

from flask_profiler import query as q

from .base import Measurement, Record, RequestMetadata, Summary

T = TypeVar("T")
SelectQueryT = TypeVar("SelectQueryT", bound="SelectQuery")


class SelectQuery(Generic[T]):
    def __init__(
        self,
        db: Cursor,
        mapping: Callable[[Any], T],
        query: q.SelectQueryImpl,
    ) -> None:
        self.mapping = mapping
        self.db = db
        self.query = query

    def _with_modified_query(
        self: SelectQueryT,
        modification: Callable[[q.SelectQueryImpl], q.SelectQueryImpl],
    ) -> SelectQueryT:
        return type(self)(
            db=self.db,
            mapping=self.mapping,
            query=modification(self.query),
        )

    def __iter__(self) -> Iterator[T]:
        results = self.db.execute(str(self.query))
        yield from map(self.mapping, results.fetchall())

    def __len__(self) -> int:
        count_query = q.SelectQueryImpl(
            from_clause=q.Alias(self.query, name=q.Identifier("subquery")),
            selector=q.SelectorList([q.Aggregate("COUNT", q.All())]),
        )
        result = self.db.execute(str(count_query))
        return result.fetchone()[0]

    def limit(self: SelectQueryT, n: int) -> SelectQueryT:
        return self._with_modified_query(lambda query: query.limit(n))

    def offset(self: SelectQueryT, n: int) -> SelectQueryT:
        return self._with_modified_query(lambda query: query.offset(n))


class RecordResult(SelectQuery[Record]):
    def summarize(self) -> SelectQuery[Summary]:
        return type(cast(SelectQuery[Summary], self))(
            db=self.db,
            query=q.SelectQueryImpl(
                selector=q.SelectorList(
                    [
                        q.Identifier("method"),
                        q.Identifier("name"),
                        q.Aggregate("COUNT", q.Identifier("id")),
                        q.Aggregate("MIN", q.Identifier("elapsed")),
                        q.Aggregate("MAX", q.Identifier("elapsed")),
                        q.Aggregate("AVG", q.Identifier("elapsed")),
                    ]
                ),
                from_clause=q.Alias(self.query, name=q.Identifier("records")),
                group_by=q.ExpressionList(
                    [
                        q.Identifier("method"),
                        q.Identifier("name"),
                    ]
                ),
            ),
            mapping=lambda row: Summary(
                method=row[0],
                name=row[1],
                count=row[2],
                min_elapsed=row[3],
                max_elapsed=row[4],
                avg_elapsed=row[5],
            ),
        )

    def with_method(self, method: str) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp("=", q.Identifier("method"), q.Literal(method))
            )
        )

    def with_name_containing(self, substring: str) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp("LIKE", q.Identifier("name"), q.Literal(f"%{substring}%"))
            )
        )

    def requested_after(self, t: datetime) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp(">=", q.Identifier("startedAt"), q.Literal(t.timestamp()))
            )
        )


class Sqlite:
    def __init__(self, sqlite_file: str, table_name: str) -> None:
        self.sqlite_file = sqlite_file
        self.table_name = table_name
        self.connection = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.lock = threading.Lock()
        try:
            self.create_database()
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e):
                raise e

    def create_database(self) -> None:
        with self.lock:
            sql = """
                CREATE TABLE {table_name} (
                    ID Integer PRIMARY KEY AUTOINCREMENT,
                    startedAt REAL,
                    endedAt REAL,
                    elapsed REAL,
                    args TEXT,
                    kwargs TEXT,
                    method TEXT,
                    context TEXT,
                    name TEXT
                );
            """.format(
                table_name=self.table_name,
            )
            self.cursor.execute(sql)

            sql = """
            CREATE INDEX measurement_index ON {table_name}
                (startedAt, endedAt, elapsed, name, method);
            """.format(
                table_name=self.table_name,
            )
            self.cursor.execute(sql)

            self.connection.commit()

    def insert(self, measurement: Measurement) -> None:
        endedAt = measurement.endedAt
        startedAt = measurement.startedAt
        elapsed = measurement.elapsed
        args = json.dumps(list(measurement.args))
        kwargs = json.dumps(measurement.kwargs)
        context = json.dumps(measurement.context.serialize_to_json())
        method = measurement.method
        name = measurement.name
        sql = """INSERT INTO {0} VALUES (
            null, ?, ?, ?, ?,?, ?, ?, ?)""".format(
            self.table_name
        )
        with self.lock:
            self.cursor.execute(
                sql, (startedAt, endedAt, elapsed, args, kwargs, method, context, name)
            )
            self.connection.commit()

    def get_records(self) -> RecordResult:
        return RecordResult(
            db=self.cursor,
            mapping=self._row_to_record,
            query=q.SelectQueryImpl(
                selector=q.SelectorList([q.All()]),
                from_clause=q.Identifier(self.table_name),
            ),
        )

    def truncate(self) -> bool:
        with self.lock:
            self.cursor.execute("DELETE FROM {0}".format(self.table_name))
            self.connection.commit()
        # True or False based on success of this delete operation
        return True if self.cursor.rowcount else False

    def _row_to_record(self, row) -> Record:
        raw_context = json.loads(row[7])
        context = RequestMetadata.from_json(raw_context)
        return Record(
            id=row[0],
            startedAt=row[1],
            endedAt=row[2],
            elapsed=row[3],
            args=json.loads(row[4]),
            kwargs=json.loads(row[5]),
            method=row[6],
            context=context,
            name=row[8],
        )
