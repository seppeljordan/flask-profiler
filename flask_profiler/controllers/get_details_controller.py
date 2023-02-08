from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PAGE_QUERY_ARGUMENT, PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_details_use_case as use_case
from flask_profiler.use_cases.get_details_use_case import GetDetailsUseCase

from .controller import Controller


class Presenter(Protocol):
    def present_response(
        self,
        response: use_case.Response,
        pagination: PaginationContext,
        http_request: HttpRequest,
    ) -> HttpResponse:
        ...


@dataclass
class GetDetailsController(Controller):
    use_case: GetDetailsUseCase
    presenter: Presenter

    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        pagination_context = self.get_pagination_context(http_request)
        form_data = FilterFormData.parse_from_from(http_request.get_arguments())
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
            response=response, pagination=pagination_context, http_request=http_request
        )

    def get_pagination_context(self, request: HttpRequest) -> PaginationContext:
        request_args = request.get_arguments()
        current_page = int(request_args.get(PAGE_QUERY_ARGUMENT, "1"))
        return PaginationContext(
            current_page=current_page,
            page_size=20,
        )
