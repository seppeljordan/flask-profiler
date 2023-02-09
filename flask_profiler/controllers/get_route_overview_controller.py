from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from flask_profiler.clock import Clock
from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse
from flask_profiler.use_cases import get_route_overview as uc


class Presenter(Protocol):
    def present_response(self, response: uc.Response) -> HttpResponse:
        ...


@dataclass
class GetRouteOverviewController:
    use_case: uc.GetRouteOverviewUseCase
    clock: Clock
    presenter: Presenter
    http_request: HttpRequest

    def handle_request(self) -> HttpResponse:
        route_name = self.http_request.path_arguments()["route_name"]
        assert isinstance(route_name, str)
        end_timestamp = self.clock.utc_now() + timedelta(days=1)
        start_timestamp = end_timestamp - timedelta(days=30)
        request = uc.Request(
            route_name=route_name,
            interval=uc.Interval.daily,
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
        return self.presenter.present_response(response)
