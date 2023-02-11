from __future__ import annotations

from dataclasses import dataclass

from flask import url_for

from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_details_use_case as use_case

from . import table
from .formatting import format_duration_in_ms
from .pagination import Paginator
from .urls import get_url_with_query

HEADERS = [
    table.Header(label="Method"),
    table.Header(label="Name"),
    table.Header(label="Response time"),
    table.Header(label="Request timestamp"),
]


@dataclass
class ViewModel:
    table: table.Table
    pagination: Paginator
    method_filter_text: str
    name_filter_text: str
    requested_after_filter_text: str
    requested_before_filter_text: str


@dataclass
class GetDetailsPresenter:
    http_request: HttpRequest

    def present_response(
        self,
        response: use_case.Response,
        pagination: PaginationContext,
    ) -> ViewModel:
        view_model = ViewModel(
            table=table.Table(
                headers=HEADERS,
                rows=[
                    [
                        table.Cell(text=measurement.method),
                        table.Cell(
                            text=measurement.name,
                            link_target=url_for(
                                ".route_overview", route_name=measurement.name
                            ),
                        ),
                        table.Cell(
                            text=format_duration_in_ms(measurement.response_time_secs)
                        ),
                        table.Cell(text=measurement.started_at.isoformat()),
                    ]
                    for measurement in response.measurements
                ],
            ),
            pagination=Paginator(
                target_link=get_url_with_query(
                    ".details", self.http_request.get_arguments()
                ),
                total_page_count=pagination.get_total_pages_count(
                    response.total_result_count
                ),
            ),
            method_filter_text=response.request.method_filter or "",
            name_filter_text=response.request.name_filter or "",
            requested_after_filter_text=""
            if response.request.requested_after is None
            else response.request.requested_after.isoformat(),
            requested_before_filter_text=""
            if response.request.requested_before is None
            else response.request.requested_before.isoformat(),
        )
        return view_model
