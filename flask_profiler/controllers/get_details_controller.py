from dataclasses import dataclass

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PAGE_QUERY_ARGUMENT, PaginationContext
from flask_profiler.presenters.get_details_presenter import GetDetailsPresenter
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases.get_details_use_case import GetDetailsUseCase
from flask_profiler.views.get_details_view import GetDetailsView

from .controller import Controller


@dataclass
class GetDetailsController(Controller):
    use_case: GetDetailsUseCase
    view: GetDetailsView
    presenter: GetDetailsPresenter

    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        pagination_context = self.get_pagination_context(http_request)
        form_data = FilterFormData.parse_from_from(http_request.get_arguments())
        request = GetDetailsUseCase.Request(
            limit=pagination_context.get_limit(),
            offset=pagination_context.get_offset(),
            requested_after=form_data.requested_after,
            name_filter=form_data.name,
            method_filter=form_data.method,
        )
        response = self.use_case.get_details(request)
        view_model = self.presenter.render_details(
            response=response, pagination=pagination_context, http_request=http_request
        )
        return self.view.render_view_model(view_model)

    def get_pagination_context(self, request: HttpRequest) -> PaginationContext:
        request_args = request.get_arguments()
        current_page = int(request_args.get(PAGE_QUERY_ARGUMENT, "1"))
        return PaginationContext(
            current_page=current_page,
            page_size=20,
        )
