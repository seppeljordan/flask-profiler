from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import ParseResult

from flask import url_for

from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_summary_use_case as use_case

from . import table
from .formatting import format_duration_in_ms
from .pagination import Paginator
from .urls import get_url_with_query


@dataclass
class ViewModel:
    table: table.Table
    pagination: Paginator
    method_filter_text: str
    name_filter_text: str
    requested_after_filter_text: str
    requested_before_filter_text: str


@dataclass
class GetSummaryPresenter:
    http_request: HttpRequest

    def render_summary(
        self,
        response: use_case.Response,
        pagination: PaginationContext,
    ) -> ViewModel:
        view_model = ViewModel(
            table=table.Table(
                headers=self.get_headers(),
                rows=[
                    self._render_row(measurement)
                    for measurement in response.measurements
                ],
            ),
            pagination=Paginator(
                total_page_count=pagination.get_total_pages_count(
                    response.total_results
                ),
                target_link=self.get_pagination_target_link(),
            ),
            method_filter_text=response.request.method or "",
            name_filter_text=response.request.name_filter or "",
            requested_after_filter_text=self._render_optional_timestamp(
                response.request.requested_after
            ),
            requested_before_filter_text=self._render_optional_timestamp(
                response.request.requested_before
            ),
        )
        return view_model

    def get_headers(self) -> List[table.Header]:
        return [
            table.Header(label="Method"),
            table.Header(label="Name"),
            table.Header(label="#Requests"),
            table.Header(
                label="Avg. response time",
                link_target=self._get_average_time_column_header_link(),
            ),
            table.Header(label="Min. response time"),
            table.Header(label="Max. response time"),
        ]

    def get_pagination_target_link(self) -> ParseResult:
        return get_url_with_query(".summary", self.http_request.get_arguments())

    def _render_row(self, measurement: use_case.Measurement) -> List[table.Cell]:
        return [
            table.Cell(text=measurement.method),
            table.Cell(
                text=measurement.name,
                link_target=url_for(".route_overview", route_name=measurement.name),
            ),
            table.Cell(text=str(measurement.request_count)),
            table.Cell(
                text=format_duration_in_ms(measurement.average_response_time_secs)
            ),
            table.Cell(text=format_duration_in_ms(measurement.min_response_time_secs)),
            table.Cell(
                text=format_duration_in_ms(measurement.max_response_time_secs),
            ),
        ]

    def _render_optional_timestamp(self, timestamp: Optional[datetime]) -> str:
        return "" if timestamp is None else timestamp.isoformat()

    def is_currently_sorted_by(self, field: use_case.SortingField) -> bool:
        mapping = {"average_time": use_case.SortingField.average_time}
        arguments = self.http_request.get_arguments()
        if sorted_by := arguments.get("sorted_by"):
            if sorted_by.startswith("+") or sorted_by.startswith("-"):
                sorted_by = sorted_by[1:]
            return mapping.get(sorted_by) == field
        return False

    def _get_average_time_column_header_link(self) -> str:
        sorted_by = "average_time"
        if self.is_currently_sorted_by(use_case.SortingField.average_time):
            sorted_by = self.alternate_sorting_order() + sorted_by
        return get_url_with_query(
            ".summary", dict(self.http_request.get_arguments(), sorted_by=sorted_by)
        ).geturl()

    def alternate_sorting_order(self) -> str:
        if sorted_by := self.http_request.get_arguments().get("sorted_by"):
            if sorted_by.startswith("-"):
                return "+"
        return "-"
