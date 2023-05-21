from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Dict, Generic, Iterator, List, Optional, TypeVar

from typing_extensions import Self

from flask_profiler.entities.measurement_archive import Measurement, Record, Summary

T = TypeVar("T")
IteratorBasedDataT = TypeVar("IteratorBasedDataT", bound="IteratorBasedData")


class FakeMeasurementArchivist:
    def __init__(self) -> None:
        self.records: List[Record] = list()

    def record_measurement(self, measurement: Measurement) -> int:
        id_ = len(self.records)
        self.records.append(
            Record(
                id=id_,
                name=measurement.route_name,
                method=measurement.method,
                start_timestamp=measurement.start_timestamp,
                end_timestamp=measurement.end_timestamp,
            )
        )
        return id_

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

    def first(self) -> Optional[T]:
        items = iter(self.items())
        try:
            return next(items)
        except StopIteration:
            return None

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

    def with_name(self, name: str) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: name == i.name, self.items())
        )

    def requested_after(self, t: datetime) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: t <= i.start_timestamp, self.items())
        )

    def requested_before(self, t: datetime) -> RecordedMeasurements:
        return replace(
            self, items=lambda: filter(lambda i: t > i.start_timestamp, self.items())
        )

    def summarize(self) -> SummarizedMeasurements:
        return SummarizedMeasurements(
            items=lambda: iter(SummaryBuilder.from_iterator(self.items()))
        )

    def summarize_by_interval(
        self, timestamps: List[datetime]
    ) -> SummarizedMeasurements:
        return SummarizedMeasurements(
            items=lambda: iter(
                IntervalSummaryBuilder.from_iterator(
                    self.items(),
                    timestamps=timestamps,
                )
            ),
        )

    def with_id(self, id_: int) -> RecordedMeasurements:
        return replace(self, items=lambda: filter(lambda i: i.id == id_, self.items()))

    def ordered_by_start_time(self, ascending: bool = True) -> RecordedMeasurements:
        return replace(
            self,
            items=lambda: sorted(
                list(self.items()),
                key=lambda measurement: measurement.start_timestamp,
                reverse=not ascending,
            ),
        )


class SummarizedMeasurements(IteratorBasedData[Summary]):
    def sorted_by_avg_elapsed(self, ascending: bool = True) -> Self:
        return replace(
            self,
            items=lambda: sorted(
                list(self.items()),
                reverse=not ascending,
                key=lambda summary: summary.avg_elapsed,
            ),
        )

    def sorted_by_route_name(self, ascending: bool = True) -> Self:
        return replace(
            self,
            items=lambda: sorted(
                list(self.items()),
                reverse=not ascending,
                key=lambda summary: summary.name,
            ),
        )


class SummaryBuilder:
    @dataclass(frozen=True)
    class SummaryKey:
        method: str
        name: str

    def __init__(self) -> None:
        self.summaries: Dict[SummaryBuilder.SummaryKey, List[Record]] = defaultdict(
            list
        )

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
            first_measurement = min(map(lambda r: r.start_timestamp, records))
            last_measurement = max(map(lambda r: r.start_timestamp, records))
            yield Summary(
                name=key.name,
                method=key.method,
                min_elapsed=min(elapsed_times),
                max_elapsed=max(elapsed_times),
                avg_elapsed=sum(elapsed_times) / len(elapsed_times),
                count=len(elapsed_times),
                first_measurement=first_measurement,
                last_measurement=last_measurement,
            )

    def record_key(self, record: Record) -> SummaryKey:
        return self.SummaryKey(
            name=record.name,
            method=record.method,
        )


class IntervalSummaryBuilder:
    @dataclass(frozen=True)
    class SummaryKey:
        method: str
        name: str
        interval_index: int

    def __init__(self, timestamps: List[datetime]) -> None:
        self.summaries: Dict[
            IntervalSummaryBuilder.SummaryKey, List[Record]
        ] = defaultdict(list)
        self.timestamps = timestamps

    def add_record(self, record: Record) -> None:
        self.summaries[self.record_key(record)].append(record)

    @classmethod
    def from_iterator(
        cls, records: Iterator[Record], timestamps: List[datetime]
    ) -> IntervalSummaryBuilder:
        builder = cls(timestamps)
        for r in records:
            if (
                r.start_timestamp < builder.timestamps[0]
                or r.start_timestamp >= builder.timestamps[-1]
            ):
                continue
            builder.add_record(r)
        return builder

    def __iter__(self) -> Iterator[Summary]:
        for key, records in self.summaries.items():
            elapsed_times = [r.elapsed for r in records]
            first_measurement = min(map(lambda r: r.start_timestamp, records))
            last_measurement = max(map(lambda r: r.start_timestamp, records))
            yield Summary(
                name=key.name,
                method=key.method,
                min_elapsed=min(elapsed_times),
                max_elapsed=max(elapsed_times),
                avg_elapsed=sum(elapsed_times) / len(elapsed_times),
                count=len(elapsed_times),
                first_measurement=first_measurement,
                last_measurement=last_measurement,
            )

    def record_key(self, record: Record) -> SummaryKey:
        interval_index = 0
        for timestamp in self.timestamps:
            if record.start_timestamp >= timestamp:
                interval_index += 1
        return self.SummaryKey(
            name=record.name,
            method=record.method,
            interval_index=interval_index,
        )
