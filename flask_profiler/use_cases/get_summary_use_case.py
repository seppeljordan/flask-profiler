from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from flask_profiler.configuration import Configuration


@dataclass
class GetSummaryUseCase:
    @dataclass
    class Measurement:
        name: str
        method: str
        request_count: int
        average_response_time_secs: float
        min_response_time_secs: float
        max_response_time_secs: float

    @dataclass
    class Request:
        limit: int
        offset: int
        method: Optional[str] = None

    @dataclass
    class Response:
        measurements: List[GetSummaryUseCase.Measurement]
        total_results: int
        request: GetSummaryUseCase.Request

    configuration: Configuration

    def get_summary(self, request: Request) -> Response:
        records = self.configuration.collection.get_records()
        if request.method is not None:
            records = records.with_method(request.method)
        results = records.summarize()
        total_results = len(results)
        results = results.limit(request.limit).offset(request.offset)
        return self.Response(
            measurements=[
                self.Measurement(
                    name=measurement.name,
                    method=measurement.method,
                    request_count=measurement.count,
                    average_response_time_secs=measurement.avg_elapsed,
                    min_response_time_secs=measurement.min_elapsed,
                    max_response_time_secs=measurement.max_elapsed,
                )
                for measurement in results
            ],
            request=request,
            total_results=total_results,
        )
