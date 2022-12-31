from dataclasses import dataclass
from urllib.parse import ParseResult

from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_summary_use_case as use_case

from . import table
from .formatting import format_duration_in_ms
from .pagination import Paginator
from .urls import get_url_with_query

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
        pagination: Paginator
        method_filter_text: str
        name_filter_text: str
        requested_after_filter_text: str

    def render_summary(
        self,
        response: use_case.Response,
        pagination: PaginationContext,
        http_request: HttpRequest,
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
            pagination=Paginator(
                total_page_count=pagination.get_total_pages_count(
                    response.total_results
                ),
                target_link=self.get_pagination_target_link(http_request),
            ),
            method_filter_text=response.request.method or "",
            name_filter_text=response.request.name_filter or "",
            requested_after_filter_text=""
            if response.request.requested_after is None
            else response.request.requested_after.isoformat(),
        )

    def get_pagination_target_link(self, http_request: HttpRequest) -> ParseResult:
        return get_url_with_query(".summary", http_request.get_arguments())
