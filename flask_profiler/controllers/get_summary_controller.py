from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PaginationContext
from flask_profiler.presenters.get_summary_presenter import GetSummaryPresenter
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_summary_use_case as uc


class Presenter(Protocol):
    def present_response(
        self,
        use_case_response: uc.Response,
        pagination: PaginationContext,
    ) -> HttpResponse:
        ...


@dataclass
class GetSummaryController:
    use_case: uc.GetSummaryUseCase
    presenter: GetSummaryPresenter
    http_request: HttpRequest

    def handle_request(self) -> HttpResponse:
        pagination = PaginationContext.from_http_request(self.http_request)
        form_data = self.parse_form_data()
        request = uc.Request(
            limit=pagination.get_limit(),
            offset=pagination.get_offset(),
            method=form_data.method,
            name_filter=form_data.name,
            requested_after=form_data.requested_after,
            requested_before=form_data.requested_before,
        )
        response = self.use_case.get_summary(request)
        return self.presenter.render_summary(response, pagination)

    def parse_form_data(self) -> FilterFormData:
        args = self.http_request.get_arguments()
        return FilterFormData.parse_from_from(args)
