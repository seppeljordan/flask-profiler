from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Iterator, Protocol, TypeVar

FiledDataT = TypeVar("FiledDataT", bound="FiledData")
T = TypeVar("T", covariant=True)


class MeasurementArchivist(Protocol):
    def record_measurement(self, measurement: Measurement) -> int:
        ...

    def get_records(self) -> RecordedMeasurements:
        ...


@dataclass
class Measurement:
    route_name: str
    start_timestamp: datetime
    end_timestamp: datetime
    method: str


class FiledData(Protocol, Generic[T]):
    def __iter__(self) -> Iterator[T]:
        ...

    def limit(self: FiledDataT, n: int) -> FiledDataT:
        ...

    def offset(self: FiledDataT, n: int) -> FiledDataT:
        ...

    def __len__(self) -> int:
        ...


@dataclass(kw_only=True)
class Record:
    id: int
    name: str
    start_timestamp: datetime
    end_timestamp: datetime
    method: str

    @property
    def elapsed(self) -> float:
        return self.end_timestamp.timestamp() - self.start_timestamp.timestamp()


class RecordedMeasurements(FiledData[Record], Protocol):
    def summarize(self) -> SummarizedMeasurements:
        ...

    def with_method(self, method: str) -> RecordedMeasurements:
        ...

    def with_name_containing(self, substring: str) -> RecordedMeasurements:
        ...

    def requested_after(self, t: datetime) -> RecordedMeasurements:
        ...

    def requested_before(self, t: datetime) -> RecordedMeasurements:
        ...

    def with_id(self, id_: int) -> RecordedMeasurements:
        ...


@dataclass(kw_only=True)
class Summary:
    method: str
    name: str
    count: int
    min_elapsed: float
    max_elapsed: float
    avg_elapsed: float
    first_measurement: datetime
    last_measurement: datetime


class SummarizedMeasurements(FiledData[Summary], Protocol):
    ...
