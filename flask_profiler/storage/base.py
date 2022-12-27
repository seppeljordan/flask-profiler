from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Iterator, Protocol, TypeVar

from flask_profiler.use_cases.measurement_archive import MeasurementArchivist

QueryResultT = TypeVar("QueryResultT", bound="QueryResult")
T = TypeVar("T", covariant=True)


class QueryResult(Protocol, Generic[T]):
    def __iter__(self) -> Iterator[T]:
        ...

    def limit(self: QueryResultT, n: int) -> QueryResultT:
        ...

    def offset(self: QueryResultT, n: int) -> QueryResultT:
        ...

    def __len__(self) -> int:
        ...


class BaseStorage(MeasurementArchivist, Protocol):
    def get_records(self) -> RecordResult:
        ...

    def truncate(self) -> bool:
        ...


DECIMAL_PLACES = 6


@dataclass(kw_only=True)
class Measurement:
    """represents an endpoint measurement"""

    name: str
    method: str
    startedAt: float
    endedAt: float

    def serialize_to_json(self) -> Any:
        return {
            "name": self.name,
            "method": self.method,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
        }

    def __str__(self):
        return str(self.serialize_to_json())

    @property
    def elapsed(self) -> float:
        return max(
            round(self.endedAt - self.startedAt, DECIMAL_PLACES),
            0.0,
        )


@dataclass(kw_only=True)
class Record:
    id: int
    name: str
    startedAt: float
    endedAt: float
    elapsed: float
    method: str


class RecordResult(QueryResult[Record], Protocol):
    def summarize(self) -> SummaryResult:
        ...

    def with_method(self, method: str) -> RecordResult:
        ...

    def with_name_containing(self, substring: str) -> RecordResult:
        ...

    def requested_after(self, t: datetime) -> RecordResult:
        ...


@dataclass(kw_only=True)
class Summary:
    method: str
    name: str
    count: int
    min_elapsed: float
    max_elapsed: float
    avg_elapsed: float


class SummaryResult(QueryResult[Summary], Protocol):
    ...
