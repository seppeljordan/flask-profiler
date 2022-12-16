from dataclasses import dataclass
from urllib.parse import urlparse

from flask import url_for

from flask_profiler.pagination import PaginationContext
from flask_profiler.use_cases.get_details_use_case import GetDetailsUseCase as UseCase

from . import table
from .formatting import format_duration_in_ms
from .pagination import Paginator

HEADERS = [
    table.Header(label="Method"),
    table.Header(label="Name"),
    table.Header(label="Response time"),
    table.Header(label="Request timestamp"),
]


class GetDetailsPresenter:
    @dataclass
    class ViewModel:
        table: table.Table
        pagination: Paginator

    def render_details(
        self, response: UseCase.Response, pagination: PaginationContext
    ) -> ViewModel:
        return self.ViewModel(
            table=table.Table(
                headers=HEADERS,
                rows=[
                    [
                        table.Cell(text=measurement.method),
                        table.Cell(text=measurement.name),
                        table.Cell(
                            text=format_duration_in_ms(measurement.response_time_secs)
                        ),
                        table.Cell(text=measurement.started_at.isoformat()),
                    ]
                    for measurement in response.measurements
                ],
            ),
            pagination=Paginator(
                target_link=urlparse(url_for(".details")),
                total_page_count=pagination.get_total_pages_count(
                    response.total_result_count
                ),
            ),
        )
