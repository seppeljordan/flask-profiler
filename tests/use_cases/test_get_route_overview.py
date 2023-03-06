from datetime import datetime, timedelta, timezone
from typing import Optional

from flask_profiler.use_cases import get_route_overview as use_case
from flask_profiler.use_cases import observe_request_handling_use_case as observe

from .base_test_case import TestCase


class GetRouteOverviewTests(TestCase):
    """These tests are written with a few assumptions in mind:

    - When no start_date is given, then start_date is assumed to be
      1.1.1999
    - When no end_date is given, then the end_date is assumed to
      1.1.2010
    """

    DEFAULT_START_DATE = datetime(1999, 1, 1, tzinfo=timezone.utc)
    DEFAULT_END_DATE = datetime(2010, 1, 1, tzinfo=timezone.utc)

    def setUp(self) -> None:
        super().setUp()
        self.use_case = self.injector.get_route_overview_use_case()
        self.observe_request_handling_use_case_factory = (
            self.injector.get_observe_request_handling_use_case_factory()
        )
        self.request_handler_factory = self.injector.get_request_handler_factory()
        self.clock = self.injector.get_clock()

    def test_that_request_is_included_in_response(self) -> None:
        self.record_measurement()
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.request == request

    def test_can_request_measurements_for_route_that_was_never_measured(
        self,
    ) -> None:
        request = self.create_request()
        self.use_case.get_route_overview(request)

    def test_can_specify_interval_daily(self) -> None:
        self.record_measurement()
        request = self.create_request(interval=use_case.Interval.daily)
        self.use_case.get_route_overview(request)

    def test_can_specify_start_time(self) -> None:
        self.record_measurement()
        request = self.create_request(start_time=datetime(2000, 1, 1))
        self.use_case.get_route_overview(request)

    def test_has_measurements_in_response_if_router_request_was_observed(self) -> None:
        self.record_measurement()
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.timeseries

    def test_that_timeseries_contains_an_entry_for_method_that_was_observed(
        self,
    ) -> None:
        self.record_measurement(method="POST")
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert response.timeseries["POST"] is not None

    def test_that_there_is_only_one_datapoint_in_response_if_one_measurement_was_observed(
        self,
    ) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_measurement(method="GET")
        request = self.create_request()
        response = self.use_case.get_route_overview(request)
        assert len(response.timeseries["GET"]) == 1

    def test_that_with_only_one_measurement_on_a_specific_day_the_value_on_that_day_is_the_duration_of_that_measurement_in_seconds(
        self,
    ) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_measurement(method="GET", duration=timedelta(seconds=3))
        request = self.create_request(
            interval=use_case.Interval.daily,
            start_time=datetime(2000, 1, 1),
            end_time=datetime(2000, 1, 2),
        )
        response = self.use_case.get_route_overview(request)
        assert response.timeseries["GET"][0].value == 3.0

    def test_that_a_measurement_on_the_following_day_at_midnight_is_ignored_for_the_day_in_question(
        self,
    ) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_measurement(method="GET", duration=timedelta(seconds=3))
        self.clock.freeze_time(datetime(2000, 1, 2))
        self.record_measurement(method="GET", duration=timedelta(seconds=1))
        request = self.create_request(
            interval=use_case.Interval.daily,
            start_time=datetime(2000, 1, 1),
            end_time=datetime(2000, 1, 2),
        )
        response = self.use_case.get_route_overview(request)
        assert response.timeseries["GET"][0].value == 3.0

    def test_that_measurements_for_other_routes_are_ignored_when_calculating_the_daily_average_value_of_a_route(
        self,
    ) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_measurement(method="GET", duration=timedelta(seconds=3))
        self.record_measurement(method="POST", duration=timedelta(seconds=1))
        request = self.create_request(
            interval=use_case.Interval.daily,
            start_time=datetime(2000, 1, 1),
            end_time=datetime(2000, 1, 2),
        )
        response = self.use_case.get_route_overview(request)
        assert response.timeseries["GET"][0].value == 3.0
        assert response.timeseries["POST"][0].value == 1.0

    def create_request(
        self,
        name: str = "test route",
        interval: Optional[use_case.Interval] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> use_case.Request:
        if start_time is None:
            start_time = self.DEFAULT_START_DATE
        if start_time.tzinfo is None:
            start_time = start_time.astimezone(timezone.utc)
        if end_time is None:
            end_time = self.DEFAULT_END_DATE
        if end_time.tzinfo is None:
            end_time = end_time.astimezone(timezone.utc)
        if interval is None:
            interval = use_case.Interval.daily
        return use_case.Request(
            route_name=name,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )

    def record_measurement(
        self, method: str = "GET", duration: Optional[timedelta] = None
    ) -> None:
        request_handler = self.request_handler_factory.create_request_handler(
            handler_name="test route", duration=duration
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
