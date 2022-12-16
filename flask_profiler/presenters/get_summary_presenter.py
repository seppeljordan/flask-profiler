from dataclasses import dataclass
from urllib.parse import urlparse

from flask import url_for

from flask_profiler.pagination import PaginationContext
from flask_profiler.use_cases.get_summary_use_case import GetSummaryUseCase as UseCase

from . import table
from .formatting import format_duration_in_ms
from .pagination import Paginator

HEADERS = [
    table.Header(label="Method"),
    table.Header(label="Name"),
    table.Header(label="#Requests"),
    table.Header(label="Avg. response time"),
    table.Header(label="Min. response time"),
    table.Header(label="Max. response time"),
]


class GetSummaryPresenter:
    @dataclass
    class ViewModel:
        table: table.Table
        method_filter_text: str
        name_filter_text: str
        requested_after_filter_text: str
        pagination: Paginator

    def render_summary(
        self, response: UseCase.Response, pagination: PaginationContext
    ) -> ViewModel:
        return self.ViewModel(
            table=table.Table(
                headers=HEADERS,
                rows=[
                    [
                        table.Cell(text=measurement.method),
                        table.Cell(text=measurement.name),
                        table.Cell(text=str(measurement.request_count)),
                        table.Cell(
                            text=format_duration_in_ms(
                                measurement.average_response_time_secs
                            )
                        ),
                        table.Cell(
                            text=format_duration_in_ms(
                                measurement.min_response_time_secs
                            )
                        ),
                        table.Cell(
                            text=format_duration_in_ms(
                                measurement.max_response_time_secs
                            ),
                        ),
                    ]
                    for measurement in response.measurements
                ],
            ),
            method_filter_text=response.request.method or "",
            name_filter_text=response.request.name_filter or "",
            pagination=Paginator(
                total_page_count=pagination.get_total_pages_count(
                    response.total_results
                ),
                target_link=urlparse(url_for(".summary")),
            ),
            requested_after_filter_text=""
            if response.request.requested_after is None
            else response.request.requested_after.isoformat(),
        )
