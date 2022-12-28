from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from flask_profiler.entities import measurement_archive


@dataclass
class Measurement:
    name: str
    method: str
    response_time_secs: float
    started_at: datetime


@dataclass
class Request:
    limit: int
    offset: int
    name_filter: Optional[str] = None
    method_filter: Optional[str] = None
    requested_after: Optional[datetime] = None
    requested_before: Optional[datetime] = None


@dataclass
class Response:
    measurements: List[Measurement]
    request: Request
    total_result_count: int


@dataclass
class GetDetailsUseCase:
    archivist: measurement_archive.MeasurementArchivist

    def get_details(self, request: Request) -> Response:
        results = self.archivist.get_records()
        if request.method_filter is not None:
            results = results.with_method(request.method_filter)
        if request.name_filter is not None:
            results = results.with_name_containing(request.name_filter)
        if request.requested_after is not None:
            results = results.requested_after(request.requested_after)
        if request.requested_before is not None:
            results = results.requested_before(request.requested_before)
        total_result_count = len(results)
        results = results.offset(request.offset).limit(request.limit)
        return Response(
            measurements=[
                Measurement(
                    name=measurement.name,
                    method=measurement.method,
                    response_time_secs=measurement.elapsed,
                    started_at=measurement.start_timestamp,
                )
                for measurement in results
            ],
            total_result_count=total_result_count,
            request=request,
        )
