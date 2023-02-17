from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from flask_profiler.clock import Clock
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_route_overview as uc


@dataclass
class GetRouteOverviewController:
    clock: Clock
    http_request: HttpRequest

    def handle_request(self) -> uc.Request:
        route_name = self.http_request.path_arguments()["route_name"]
        assert isinstance(route_name, str)
        end_timestamp = self.clock.utc_now() + timedelta(days=1)
        start_timestamp = end_timestamp - timedelta(days=30)
        return uc.Request(
            route_name=route_name,
            interval=uc.Interval.daily,
            start_time=start_timestamp,
            end_time=end_timestamp,
        )
