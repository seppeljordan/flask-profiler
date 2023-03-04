from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from sqlite3 import Cursor
from typing import Any, Callable, Generic, Iterator, List, TypeVar, cast
from urllib.parse import quote

from flask_profiler import query as q
from flask_profiler.entities import measurement_archive as interface

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
        if self.query.limit_clause < 0:
            new_limit = n
        else:
            new_limit = min(max(0, n), self.query.limit_clause)
        return replace(
            self,
            query=replace(
                self.query,
                limit_clause=new_limit,
            ),
        )

    def offset(self: SelectQueryT, n: int) -> SelectQueryT:
        if self.query.offset_clause < 0:
            new_offset = n
        else:
            new_offset = self.query.offset_clause + n
        return replace(
            self,
            query=replace(
                self.query,
                offset_clause=new_offset,
            ),
        )


class RecordResult(SelectQuery[interface.Record]):
    def summarize(self) -> SelectQuery[interface.Summary]:
        return replace(
            cast(SelectQuery[interface.Summary], self),
            query=q.Select(
                selector=q.SelectorList(
                    [
                        q.Identifier("method"),
                        q.Identifier("route_name"),
                        q.Alias(
                            q.Aggregate("MIN", q.Identifier("start_timestamp")),
                            q.Identifier("first_measurement_timestamp"),
                        ),
                        q.Alias(
                            q.Aggregate("MAX", q.Identifier("start_timestamp")),
                            q.Identifier("last_measurement_timestamp"),
                        ),
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
                        q.Identifier("route_name"),
                    ]
                ),
            ),
            mapping=self.summary_mapping,
        )

    def summarize_by_interval(
        self, timestamps: List[datetime]
    ) -> SelectQuery[interface.Summary]:
        first_timestamp = timestamps[0]
        last_timestamp = timestamps[-1]
        interval_op: q.Expression = q.If(
            q.BinaryOp(
                "<",
                q.Identifier("start_timestamp"),
                q.Literal(timestamps[0].timestamp()),
            ),
            q.Literal(0),
            q.Literal(1),
        )
        for timestamp in timestamps[1:]:
            interval_op = q.BinaryOp(
                "+",
                q.If(
                    q.BinaryOp(
                        "<",
                        q.Identifier("start_timestamp"),
                        q.Literal(timestamp.timestamp()),
                    ),
                    q.Literal(0),
                    q.Literal(1),
                ),
                interval_op,
            )
        return replace(
            cast(SelectQuery[interface.Summary], self),
            query=q.Select(
                selector=q.SelectorList(
                    [
                        q.Identifier("method"),
                        q.Identifier("route_name"),
                        q.Alias(
                            q.Aggregate("MIN", q.Identifier("start_timestamp")),
                            q.Identifier("first_measurement_timestamp"),
                        ),
                        q.Alias(
                            q.Aggregate("MAX", q.Identifier("start_timestamp")),
                            q.Identifier("last_measurement_timestamp"),
                        ),
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
                        q.Alias(
                            interval_op,
                            q.Identifier("interval_count"),
                        ),
                    ]
                ),
                from_clause=q.Alias(
                    self.requested_after(first_timestamp)
                    .requested_before(last_timestamp)
                    .query,
                    name=q.Identifier("records"),
                ),
                group_by=q.ExpressionList(
                    [
                        q.Identifier("method"),
                        q.Identifier("route_name"),
                        q.Identifier("interval_count"),
                    ]
                ),
            ),
            mapping=self.summary_mapping,
        )

    @classmethod
    def summary_mapping(cls, row: Any) -> interface.Summary:
        return interface.Summary(
            method=row["method"],
            name=row["route_name"],
            count=row["count"],
            min_elapsed=row["min"],
            max_elapsed=row["max"],
            avg_elapsed=row["avg"],
            first_measurement=datetime.fromtimestamp(
                row["first_measurement_timestamp"], tz=timezone.utc
            ),
            last_measurement=datetime.fromtimestamp(
                row["last_measurement_timestamp"], tz=timezone.utc
            ),
        )

    def with_method(self, method: str) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp("=", q.Identifier("method"), q.Literal(quote(method)))
            )
        )

    def with_name(self, name: str) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp("=", q.Identifier("route_name"), q.Literal(quote(name)))
            )
        )

    def with_name_containing(self, substring: str) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp(
                    "LIKE",
                    q.Identifier("route_name"),
                    q.Literal(f"%{quote(substring)}%"),
                )
            )
        )

    def requested_after(self, t: datetime) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp(
                    ">=", q.Identifier("start_timestamp"), q.Literal(t.timestamp())
                )
            )
        )

    def requested_before(self, t: datetime) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp(
                    "<", q.Identifier("start_timestamp"), q.Literal(t.timestamp())
                )
            )
        )

    def with_id(self, id_: int) -> RecordResult:
        return self._with_modified_query(
            lambda query: query.and_where(
                q.BinaryOp("=", q.Identifier("ID"), q.Literal(id_))
            )
        )
