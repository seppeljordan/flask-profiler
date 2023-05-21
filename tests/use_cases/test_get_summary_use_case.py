from datetime import datetime, timedelta, timezone
from typing import Optional

from flask_profiler.use_cases import get_summary_use_case as use_case
from flask_profiler.use_cases import observe_request_handling_use_case as observe

from .base_test_case import TestCase


class UseCaseTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_case = self.injector.get_summary_use_case()
        self.observe_request_use_case_factory = (
            self.injector.get_observe_request_handling_use_case_factory()
        )
        self.request_handler_factory = self.injector.get_request_handler_factory()
        self.clock = self.injector.get_clock()

    def test_with_nothing_recorded_total_result_count_is_0(self) -> None:
        response = self.use_case.get_summary(self.get_uc_request())
        assert not response.total_results

    def test_with_one_request_recorded_total_result_count_is_1(self) -> None:
        self.record_request()
        response = self.use_case.get_summary(self.get_uc_request())
        assert response.total_results == 1

    def test_with_three_identical_requests_recorded_total_result_count_is_1(
        self,
    ) -> None:
        self.record_request()
        self.record_request()
        self.record_request()
        response = self.use_case.get_summary(self.get_uc_request())
        assert response.total_results == 1

    def test_can_exclude_records_from_summary_via_requested_before(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 2))
        self.record_request()
        request = self.get_uc_request(
            requested_before=datetime(2000, 1, 1, tzinfo=timezone.utc)
        )
        response = self.use_case.get_summary(request)
        assert not response.total_results

    def test_can_sort_by_average_time_in_descending_order(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_request(route_name="shorter handler", duration=timedelta(seconds=1))
        self.record_request(route_name="longer handler", duration=timedelta(seconds=2))
        response = self.use_case.get_summary(
            self.get_uc_request(
                sorting_field=use_case.SortingField.average_time,
                sorting_order=use_case.SortingOrder.descending,
            )
        )
        assert [measurement.name for measurement in response.measurements] == [
            "longer handler",
            "shorter handler",
        ]

    def test_can_sort_by_average_time_in_ascending_order(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 1))
        self.record_request(route_name="shorter handler", duration=timedelta(seconds=1))
        self.record_request(route_name="longer handler", duration=timedelta(seconds=2))
        response = self.use_case.get_summary(
            self.get_uc_request(
                sorting_field=use_case.SortingField.average_time,
                sorting_order=use_case.SortingOrder.ascending,
            )
        )
        assert [measurement.name for measurement in response.measurements] == [
            "shorter handler",
            "longer handler",
        ]

    def record_request(
        self,
        route_name: Optional[str] = None,
        duration: timedelta = timedelta(seconds=1),
    ) -> None:
        if route_name is None:
            route_name = "test handler"
        request_handler = self.request_handler_factory.create_request_handler(
            handler_name=route_name, duration=duration
        )
        observe_request_use_case = (
            self.observe_request_use_case_factory.create_use_case(
                request_handler=request_handler,
            )
        )
        observe_request_use_case.record_measurement(
            request=observe.Request(
                request_args=tuple(),
                request_kwargs=dict(),
                method="GET",
            )
        )

    def get_uc_request(
        self,
        requested_before: Optional[datetime] = None,
        sorting_order: use_case.SortingOrder = use_case.SortingOrder.ascending,
        sorting_field: use_case.SortingField = use_case.SortingField.none,
    ) -> use_case.Request:
        return use_case.Request(
            sorting_field=sorting_field,
            sorting_order=sorting_order,
            limit=10,
            offset=10,
            requested_before=requested_before,
        )
