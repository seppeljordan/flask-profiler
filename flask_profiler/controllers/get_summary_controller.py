from __future__ import annotations

from dataclasses import dataclass

from flask_profiler.pagination import PAGE_QUERY_ARGUMENT, PaginationContext
from flask_profiler.presenters.get_summary_presenter import GetSummaryPresenter
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases.get_summary_use_case import GetSummaryUseCase
from flask_profiler.views.get_summary_view import GetSummaryView

from .controller import Controller


@dataclass
class GetSummaryController(Controller):
    use_case: GetSummaryUseCase
    presenter: GetSummaryPresenter
    view: GetSummaryView

    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        pagination = self.get_pagination_context(http_request)
        args = http_request.get_arguments()
        method = args.get("method") or None
        if method:
            method = method.upper()
        request = GetSummaryUseCase.Request(limit=100, offset=0, method=method)
        return self._process_request(request, pagination)

    def _process_request(
        self, request: GetSummaryUseCase.Request, pagination: PaginationContext
    ) -> HttpResponse:
        response = self.use_case.get_summary(request)
        view_model = self.presenter.render_summary(response, pagination)
        return self.view.render_view_model(view_model)

    def get_pagination_context(self, request: HttpRequest) -> PaginationContext:
        request_args = request.get_arguments()
        current_page = int(request_args.get(PAGE_QUERY_ARGUMENT, "1"))
        return PaginationContext(
            current_page=current_page,
            page_size=20,
        )
