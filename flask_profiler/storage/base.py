from __future__ import annotations

import enum
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple


class BaseStorage(Protocol):
    def filter(self, criteria: FilterQuery) -> List[Record]:
        ...

    def get_summary(self, criteria: FilterQuery) -> List[Summary]:
        ...

    def insert(self, measurement: Measurement) -> None:
        ...

    def truncate(self) -> bool:
        ...

    def get_timeseries(
        self, started_at: float, ended_at: float, interval: str
    ) -> Dict[float, int]:
        ...

    def get_method_distribution(
        self, started_at: float, ended_at: float
    ) -> Dict[str, int]:
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
class FilterQuery:
    limit: int
    skip: int
    sort: Tuple[str, str]
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None
    elapsed: Optional[float] = None
    name: Optional[str] = None
    method: Optional[str] = None
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None


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

    def serialize_to_json(self) -> Any:
        data = {
            "id": self.id,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "args": tuple(self.args),
            "kwargs": self.kwargs,
            "method": self.method,
            "context": self.context.serialize_to_json(),
            "name": self.name,
        }

        return data


@dataclass(kw_only=True)
class Summary:
    method: str
    name: str
    count: int
    min_elapsed: float
    max_elapsed: float
    avg_elapsed: float

    def serialize_to_json(self) -> Any:
        return dict(
            method=self.method,
            name=self.name,
            count=self.count,
            minElapsed=self.min_elapsed,
            maxElapsed=self.max_elapsed,
            avgElapsed=self.avg_elapsed,
        )
