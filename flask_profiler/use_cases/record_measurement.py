from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .measurement_archive import Measurement, MeasurementArchivist


@dataclass
class Request:
    route_name: str
    start_timestamp: datetime
    end_timestamp: datetime
    method: str


@dataclass
class RecordMeasurementUseCase:
    archive: MeasurementArchivist

    def record_measurement(self, request: Request):
        self.archive.record_measurement(
            Measurement(
                route_name=request.route_name,
                start_timestamp=request.start_timestamp,
                end_timestamp=request.end_timestamp,
                method=request.method,
            )
        )
