from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from flask_profiler.entities import measurement_archive


class SortingField(enum.Enum):
    average_time = enum.auto()
    route_name = enum.auto()
    none = enum.auto()


class SortingOrder(enum.Enum):
    ascending = enum.auto()
    descending = enum.auto()


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
    sorting_order: SortingOrder
    sorting_field: SortingField
    method: Optional[str] = None
    name_filter: Optional[str] = None
    requested_after: Optional[datetime] = None
    requested_before: Optional[datetime] = None


@dataclass
class Response:
    measurements: List[Measurement]
    total_results: int
    request: Request


@dataclass
class GetSummaryUseCase:
    archivist: measurement_archive.MeasurementArchivist

    def get_summary(self, request: Request) -> Response:
        records = self.archivist.get_records()
        if request.method is not None:
            records = records.with_method(request.method)
        if request.name_filter is not None:
            records = records.with_name_containing(request.name_filter)
        if request.requested_after is not None:
            records = records.requested_after(request.requested_after)
        if request.requested_before is not None:
            records = records.requested_before(request.requested_before)
        results = records.summarize()
        if request.sorting_field == SortingField.average_time:
            results = results.sorted_by_avg_elapsed(
                ascending=request.sorting_order == SortingOrder.ascending
            )
        elif request.sorting_field == SortingField.route_name:
            results = results.sorted_by_route_name(
                ascending=request.sorting_order == SortingOrder.ascending
            )
        total_results = len(results)
        results = results.limit(request.limit).offset(request.offset)
        return Response(
            measurements=[
                Measurement(
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
