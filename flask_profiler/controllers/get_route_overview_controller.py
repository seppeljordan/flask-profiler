from dataclasses import dataclass
from datetime import timedelta

from flask_profiler.clock import Clock
from flask_profiler.presenters import get_route_overview_presenter as presenter
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_route_overview
from flask_profiler.views import get_route_overview_view as view

from .controller import Controller


@dataclass
class GetRouteOverviewController(Controller):
    use_case: get_route_overview.GetRouteOverviewUseCase
    clock: Clock
    presenter: presenter.GetRouteOverviewPresenter
    view: view.GetRouteOverviewView

    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        route_name = http_request.path_arguments()["route_name"]
        assert isinstance(route_name, str)
        end_timestamp = self.clock.utc_now() + timedelta(days=1)
        start_timestamp = end_timestamp - timedelta(days=30)
        request = get_route_overview.Request(
            route_name=route_name,
            interval=get_route_overview.Interval.daily,
            start_time=start_timestamp,
            end_time=end_timestamp,
        )
        try:
            response = self.use_case.get_route_overview(request)
        except ValueError:
            return HttpResponse(
                status_code=404,
                content="NOT FOUND",
            )
        view_model = self.presenter.render_route_overview(response)
        return self.view.render_view_model(view_model)
