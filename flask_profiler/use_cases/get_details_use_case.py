from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from flask_profiler.configuration import Configuration


@dataclass
class GetDetailsUseCase:
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

    @dataclass
    class Response:
        measurements: List[GetDetailsUseCase.Measurement]
        request: GetDetailsUseCase.Request
        total_result_count: int

    configuration: Configuration

    def get_details(self, request: Request) -> Response:
        results = self.configuration.collection.get_records()
        if request.method_filter is not None:
            results = results.with_method(request.method_filter)
        if request.name_filter is not None:
            results = results.with_name_containing(request.name_filter)
        if request.requested_after is not None:
            results = results.requested_after(request.requested_after)
        total_result_count = len(results)
        results = results.offset(request.offset).limit(request.limit)
        return self.Response(
            measurements=[
                self.Measurement(
                    name=measurement.name,
                    method=measurement.method,
                    response_time_secs=measurement.elapsed,
                    started_at=datetime.fromtimestamp(measurement.startedAt),
                )
                for measurement in results
            ],
            total_result_count=total_result_count,
            request=request,
        )
