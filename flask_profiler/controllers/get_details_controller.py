from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_details_use_case as use_case
from flask_profiler.use_cases.get_details_use_case import GetDetailsUseCase


class Presenter(Protocol):
    def present_response(
        self,
        response: use_case.Response,
        pagination: PaginationContext,
    ) -> HttpResponse:
        ...


@dataclass
class GetDetailsController:
    use_case: GetDetailsUseCase
    presenter: Presenter
    http_request: HttpRequest

    def handle_request(self) -> HttpResponse:
        pagination_context = PaginationContext.from_http_request(self.http_request)
        form_data = FilterFormData.parse_from_from(self.http_request.get_arguments())
        request = use_case.Request(
            limit=pagination_context.get_limit(),
            offset=pagination_context.get_offset(),
            requested_after=form_data.requested_after,
            requested_before=form_data.requested_before,
            name_filter=form_data.name,
            method_filter=form_data.method,
        )
        response = self.use_case.get_details(request)
        return self.presenter.present_response(
            response=response, pagination=pagination_context
        )
