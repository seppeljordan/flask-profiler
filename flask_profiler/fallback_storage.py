from __future__ import annotations

from datetime import datetime
from typing import Iterator

from flask_profiler.entities import measurement_archive as archive


class MeasurementArchivistPlaceholder:
    def record_measurement(self, measurement: archive.Measurement) -> None:
        pass

    def get_records(self) -> RecordedMeasurementsPlaceholder:
        return RecordedMeasurementsPlaceholder()

    def close_connection(self) -> None:
        pass


class RecordedMeasurementsPlaceholder:
    def __iter__(self) -> Iterator[archive.Record]:
        return iter([])

    def limit(self, n: int) -> RecordedMeasurementsPlaceholder:
        return self

    def offset(self, n: int) -> RecordedMeasurementsPlaceholder:
        return self

    def __len__(self) -> int:
        return 0

    def summarize(self) -> SummarizedMeasurementsPlaceholder:
        return SummarizedMeasurementsPlaceholder()

    def with_method(self, method: str) -> RecordedMeasurementsPlaceholder:
        return self

    def with_name_containing(self, substring: str) -> RecordedMeasurementsPlaceholder:
        return self

    def requested_after(self, t: datetime) -> RecordedMeasurementsPlaceholder:
        return self

    def requested_before(self, t: datetime) -> RecordedMeasurementsPlaceholder:
        return self


class SummarizedMeasurementsPlaceholder:
    def __iter__(self) -> Iterator[archive.Summary]:
        return iter([])

    def limit(self, n: int) -> SummarizedMeasurementsPlaceholder:
        return self

    def offset(self, n: int) -> SummarizedMeasurementsPlaceholder:
        return self

    def __len__(self) -> int:
        return 0
