from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Dict, Generic, Iterator, List, TypeVar

from flask_profiler.use_cases.measurement_archive import Measurement, Record, Summary

T = TypeVar("T")
IteratorBasedDataT = TypeVar("IteratorBasedDataT", bound="IteratorBasedData")


class FakeMeasurementArchivist:
    def __init__(self) -> None:
        self.records: List[Record] = list()

    def record_measurement(self, measurement: Measurement) -> None:
        self.records.append(
            Record(
                id=len(self.records),
                name=measurement.route_name,
                method=measurement.method,
                start_timestamp=measurement.start_timestamp,
                end_timestamp=measurement.end_timestamp,
            )
        )

    def get_records(self) -> RecordedMeasurements:
        return RecordedMeasurements(items=lambda: iter(self.records))


@dataclass
class IteratorBasedData(Generic[T]):
    items: Callable[[], Iterator[T]]

    def __iter__(self) -> Iterator[T]:
        return self.items()

    def limit(self: IteratorBasedDataT, n: int) -> IteratorBasedDataT:
        return replace(self, items=lambda: itertools.islice(self.items(), 0, n))

    def offset(self: IteratorBasedDataT, n: int) -> IteratorBasedDataT:
        return replace(
            self,
            items=lambda: itertools.islice(self.items(), n),
        )

    def __len__(self) -> int:
        i = 0
        for _ in self.items():
            i += 1
        return i


class RecordedMeasurements(IteratorBasedData[Record]):
    def with_method(self, method: str) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: i.method == method, self.items())
        )

    def with_name_containing(self, substring: str) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: substring in i.name, self.items())
        )

    def requested_after(self, t: datetime) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: t <= i.start_timestamp, self.items())
        )

    def summarize(self) -> SummarizedMeasurements:
        return SummarizedMeasurements(
            items=lambda: iter(SummaryBuilder.from_iterator(self.items()))
        )


class SummarizedMeasurements(IteratorBasedData[Summary]):
    pass


@dataclass(frozen=True)
class SummaryKey:
    method: str
    name: str


class SummaryBuilder:
    def __init__(self) -> None:
        self.summaries: Dict[SummaryKey, List[Record]] = defaultdict(list)

    def add_record(self, record: Record) -> None:
        self.summaries[self.record_key(record)].append(record)

    @classmethod
    def from_iterator(cls, records: Iterator[Record]) -> SummaryBuilder:
        builder = cls()
        for r in records:
            builder.add_record(r)
        return builder

    def __iter__(self) -> Iterator[Summary]:
        for key, records in self.summaries.items():
            elapsed_times = [r.elapsed for r in records]
            yield Summary(
                name=key.name,
                method=key.method,
                min_elapsed=min(elapsed_times),
                max_elapsed=max(elapsed_times),
                avg_elapsed=sum(elapsed_times) / len(elapsed_times),
                count=len(elapsed_times),
            )

    def record_key(self, record: Record) -> SummaryKey:
        return SummaryKey(
            name=record.name,
            method=record.method,
        )
