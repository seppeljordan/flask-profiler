from datetime import datetime
from typing import Optional

from flask_profiler.use_cases import get_route_overview as use_case
from flask_profiler.use_cases import observe_request_handling_use_case as observe

from .base_test_case import TestCase


class GetRouteOverviewTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_case = self.injector.get_route_overview_use_case()
        self.observe_request_handling_use_case_factory = (
            self.injector.get_observe_request_handling_use_case_factory()
        )
        self.request_handler_factory = self.injector.get_request_handler_factory()
        self.clock = self.injector.get_clock()

    def test_that_request_is_included_in_response(self) -> None:
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.request == request

    def test_that_there_are_no_timeseries_in_response_if_no_measurements_where_made(
        self,
    ) -> None:
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert not response.timeseries

    def test_can_specify_interval_daily(self) -> None:
        request = self.create_request(interval=use_case.Interval.daily)
        self.use_case.get_route_overview(request)

    def test_can_specify_interval_weekly(self) -> None:
        request = self.create_request(interval=use_case.Interval.weekly)
        self.use_case.get_route_overview(request)

    def test_can_specify_interval_montly(self) -> None:
        request = self.create_request(interval=use_case.Interval.monthly)
        self.use_case.get_route_overview(request)

    def test_can_specify_start_time(self) -> None:
        request = self.create_request(start_time=datetime(2000, 1, 1))
        self.use_case.get_route_overview(request)

    def test_has_measurements_in_response_if_router_request_was_observed(self) -> None:
        self.record_measurement()
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.timeseries

    def test_no_measurements_in_response_if_only_requests_for_other_routes_were_observed(
        self,
    ) -> None:
        self.record_measurement()
        request = self.create_request(name="other route")
        response = self.use_case.get_route_overview(request)
        assert not response.timeseries

    def test_that_timeseries_contain_an_entry_for_method_that_was_observed(
        self,
    ) -> None:
        self.record_measurement(method="POST")
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.timeseries["POST"]

    def create_request(
        self,
        name: str = "test route",
        interval: Optional[use_case.Interval] = None,
        start_time: Optional[datetime] = None,
    ) -> use_case.Request:
        if interval is None:
            interval = use_case.Interval.daily
        return use_case.Request(
            route_name=name, interval=interval, start_time=start_time
        )

    def record_measurement(self, method: str = "GET") -> None:
        request_handler = self.request_handler_factory.create_request_handler(
            handler_name="test route"
        )
        use_case = self.observe_request_handling_use_case_factory.create_use_case(
            request_handler=request_handler
        )
        use_case.record_measurement(
            observe.Request(
                request_args=tuple(),
                request_kwargs=dict(),
                method=method,
            )
        )
