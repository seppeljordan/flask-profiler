from __future__ import annotations

import enum
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Generic, Iterator, List, Protocol, TypeVar

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


class BaseStorage(Protocol):
    def get_records(self) -> RecordResult:
        ...

    def insert(self, measurement: Measurement) -> None:
        ...

    def truncate(self) -> bool:
        ...


@enum.unique
class RecordSortColumn(enum.Enum):
    method = enum.auto()
    route_name = enum.auto()
    started_at = enum.auto()
    elapsed = enum.auto()


@enum.unique
class SummarySortColumn(enum.Enum):
    method = enum.auto()
    route_name = enum.auto()
    count = enum.auto()
    average_elapsed = enum.auto()
    min_elapsed = enum.auto()
    max_elapsed = enum.auto()


@enum.unique
class SortDirection(enum.Enum):
    ascending = enum.auto()
    descending = enum.auto()


@dataclass(kw_only=True)
class RequestMetadata:
    url: str
    args: Dict[str, str]
    form: Dict[str, str]
    headers: Dict[str, str]
    endpoint_name: str
    client_address: str

    def serialize_to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, json_object: Any) -> RequestMetadata:
        if json_object.get("endpoint_name") is not None:
            endpoint_name = json_object["endpoint_name"]
        else:
            endpoint_name = json_object["func"]

        if json_object.get("client_address") is not None:
            client_address = json_object["client_address"]
        else:
            client_address = json_object["ip"]
        return cls(
            url=json_object["url"],
            args=json_object["args"],
            form=json_object["form"],
            headers=json_object["headers"],
            endpoint_name=endpoint_name,
            client_address=client_address,
        )


DECIMAL_PLACES = 6


@dataclass(kw_only=True)
class Measurement:
    """represents an endpoint measurement"""

    context: RequestMetadata
    name: str
    method: str
    args: List[str]
    kwargs: Dict[str, str]
    startedAt: float
    endedAt: float

    def serialize_to_json(self):
        return {
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "method": self.method,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "context": self.context.serialize_to_json(),
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
    args: List[str]
    kwargs: Dict[str, Any]
    method: str
    context: RequestMetadata


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
