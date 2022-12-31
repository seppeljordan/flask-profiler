from __future__ import annotations

from dataclasses import dataclass

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PAGE_QUERY_ARGUMENT, PaginationContext
from flask_profiler.presenters.get_summary_presenter import GetSummaryPresenter
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_summary_use_case as uc
from flask_profiler.views.get_summary_view import GetSummaryView

from .controller import Controller


@dataclass
class GetSummaryController(Controller):
    use_case: uc.GetSummaryUseCase
    presenter: GetSummaryPresenter
    view: GetSummaryView

    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        pagination = self.get_pagination_context(http_request)
        form_data = self.parse_form_data(http_request)
        request = uc.Request(
            limit=pagination.get_limit(),
            offset=pagination.get_offset(),
            method=form_data.method,
            name_filter=form_data.name,
            requested_after=form_data.requested_after,
        )
        return self._process_request(request, pagination, http_request)

    def _process_request(
        self,
        request: uc.Request,
        pagination: PaginationContext,
        http_request: HttpRequest,
    ) -> HttpResponse:
        response = self.use_case.get_summary(request)
        view_model = self.presenter.render_summary(response, pagination, http_request)
        return self.view.render_view_model(view_model)

    def get_pagination_context(self, request: HttpRequest) -> PaginationContext:
        request_args = request.get_arguments()
        current_page = int(request_args.get(PAGE_QUERY_ARGUMENT, "1"))
        return PaginationContext(
            current_page=current_page,
            page_size=20,
        )

    def parse_form_data(self, http_request: HttpRequest) -> FilterFormData:
        args = http_request.get_arguments()
        return FilterFormData.parse_from_from(args)
