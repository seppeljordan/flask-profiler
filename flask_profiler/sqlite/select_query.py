from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from datetime import datetime
from sqlite3 import Cursor
from typing import Any, Callable, Generic, Iterator, TypeVar, cast

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
        return self._with_modified_query(lambda query: query.limit(n))

    def offset(self: SelectQueryT, n: int) -> SelectQueryT:
        return self._with_modified_query(lambda query: query.offset(n))


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
            mapping=lambda row: interface.Summary(
                method=row["method"],
                name=row["route_name"],
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
                q.BinaryOp(
                    "LIKE", q.Identifier("route_name"), q.Literal(f"%{substring}%")
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
