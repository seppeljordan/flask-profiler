from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from sqlite3 import Cursor
from typing import Any, Callable, Dict, Generic, Iterator, TypeVar, cast

from flask_profiler import query as q
from flask_profiler.storage.base import Measurement, Record, RequestMetadata, Summary

from .migrations import Migrations

T = TypeVar("T")
SelectQueryT = TypeVar("SelectQueryT", bound="SelectQuery")


LOGGER = logging.getLogger(__name__)


@dataclass
class SelectQuery(Generic[T]):
    mapping: Callable[[Any], T]
    db: Cursor
    query: q.Select

    def _with_modified_query(
        self: SelectQueryT,
        modification: Callable[[q.Select], q.Select],
    ) -> SelectQueryT:
        return replace(self, query=modification(self.query))

    def __iter__(self) -> Iterator[T]:
        LOGGER.debug("Running query %s", self.query)
        results = self.db.execute(str(self.query))
        yield from map(self.mapping, results.fetchall())

    def __len__(self) -> int:
        count_query = q.Select(
            from_clause=q.Alias(self.query, name=q.Identifier("subquery")),
            selector=q.SelectorList([q.Aggregate("COUNT", q.All())]),
        )
        LOGGER.debug("Running query %s", count_query)
        result = self.db.execute(str(count_query))
        return result.fetchone()[0]

    def limit(self: SelectQueryT, n: int) -> SelectQueryT:
        return self._with_modified_query(lambda query: query.limit(n))

    def offset(self: SelectQueryT, n: int) -> SelectQueryT:
        return self._with_modified_query(lambda query: query.offset(n))


class RecordResult(SelectQuery[Record]):
    def summarize(self) -> SelectQuery[Summary]:
        return replace(
            cast(SelectQuery[Summary], self),
            query=q.Select(
                selector=q.SelectorList(
                    [
                        q.Identifier("method"),
                        q.Identifier("name"),
                        q.Alias(
                            q.Aggregate("COUNT", q.Identifier("id")),
                            q.Identifier("count"),
                        ),
                        q.Alias(
                            q.Aggregate("MIN", q.Identifier("elapsed")),
                            q.Identifier("min"),
                        ),
                        q.Alias(
                            q.Aggregate("MAX", q.Identifier("elapsed")),
                            q.Identifier("max"),
                        ),
                        q.Alias(
                            q.Aggregate("AVG", q.Identifier("elapsed")),
                            q.Identifier("avg"),
                        ),
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
                method=row["method"],
                name=row["name"],
                count=row["count"],
                min_elapsed=row["min"],
                max_elapsed=row["max"],
                avg_elapsed=row["avg"],
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
    def __init__(self, sqlite_file: str) -> None:
        self.sqlite_file = sqlite_file
        self.connection = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self.create_database()

    def create_database(self) -> None:
        migrations = Migrations(self.connection)
        migrations.run_necessary_migrations()

    def insert(self, measurement: Measurement) -> None:
        endedAt = measurement.endedAt
        startedAt = measurement.startedAt
        elapsed = measurement.elapsed
        context = json.dumps(measurement.context.serialize_to_json())
        method = measurement.method
        name = measurement.name
        query = q.Insert(
            into=q.Identifier("measurements"),
            columns=[
                q.Identifier("startedAt"),
                q.Identifier("endedAt"),
                q.Identifier("elapsed"),
                q.Identifier("method"),
                q.Identifier("context"),
                q.Identifier("name"),
            ],
            rows=[
                [
                    q.Literal(startedAt),
                    q.Literal(endedAt),
                    q.Literal(elapsed),
                    q.Literal(method),
                    q.Literal(context),
                    q.Literal(name),
                ]
            ],
            returning=q.All(),
        )
        result = self.cursor.execute(str(query))
        measurement_id = result.fetchone()[0]
        if measurement.kwargs:
            kwargs_query = q.Insert(
                into=q.Identifier("keyword_arguments"),
                columns=[
                    q.Identifier("measurement"),
                    q.Identifier("key"),
                    q.Identifier("value"),
                ],
                rows=[
                    [
                        q.Literal(measurement_id),
                        q.Literal(key),
                        q.Literal(value),
                    ]
                    for key, value in measurement.kwargs.items()
                ],
            )
            self.cursor.execute(str(kwargs_query))
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
                            expression=concat_key_value_pairs(
                                table="keyword_arguments"
                            ),
                            name=q.Identifier("keyword_args"),
                        ),
                    ]
                ),
                from_clause=q.Join(
                    table=q.Identifier("measurements"),
                    spec=[
                        q.left(
                            table=q.Identifier("keyword_arguments"),
                            constraint=q.On(
                                q.BinaryOp(
                                    "=", q.Identifier("ID"), q.Identifier("measurement")
                                )
                            ),
                        ),
                    ],
                ),
                group_by=q.ExpressionList(
                    [
                        q.Identifier("ID"),
                    ]
                ),
            ),
        )

    def truncate(self) -> bool:
        statement = q.Delete(q.Identifier("measurements"))
        self.cursor.execute(statement.as_statement())
        self.connection.commit()
        return True if self.cursor.rowcount else False

    def _row_to_record(self, row) -> Record:
        raw_context = json.loads(row["context"])
        context = RequestMetadata.from_json(raw_context)
        keyword_arguments: Dict[str, str] = dict()
        if row["keyword_args"]:
            for record in row["keyword_args"].split("\u001d"):
                try:
                    key, value = record.split("\u001e", maxsplit=1)
                except ValueError:
                    continue
        return Record(
            id=row["ID"],
            startedAt=row["startedAt"],
            endedAt=row["endedAt"],
            elapsed=row["elapsed"],
            kwargs=keyword_arguments,
            method=row["method"],
            context=context,
            name=row["name"],
        )


def concat_key_value_pairs(table: str, key: str = "key", value: str = "value"):
    return q.Aggregate(
        "GROUP_CONCAT",
        q.ExpressionList(
            [
                q.BinaryOp(
                    "||",
                    q.Identifier([table, key]),
                    q.BinaryOp(
                        "||",
                        q.Literal("\u001e"),
                        q.Identifier([table, value]),
                    ),
                ),
                q.Literal("\u001d"),
            ]
        ),
    )
