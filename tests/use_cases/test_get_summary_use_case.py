from datetime import datetime

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
        request = use_case.Request(limit=10, offset=10)
        response = self.use_case.get_summary(request)
        assert not response.total_results

    def test_with_one_request_recorded_total_result_count_is_1(self) -> None:
        self.record_request()
        request = use_case.Request(limit=10, offset=10)
        response = self.use_case.get_summary(request)
        assert response.total_results == 1

    def test_with_three_identical_requests_recorded_total_result_count_is_1(
        self,
    ) -> None:
        self.record_request()
        self.record_request()
        self.record_request()
        request = use_case.Request(limit=10, offset=10)
        response = self.use_case.get_summary(request)
        assert response.total_results == 1

    def test_can_exclude_records_from_summary_via_requested_before(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 2))
        self.record_request()
        request = use_case.Request(
            limit=10, offset=10, requested_before=datetime(2000, 1, 1)
        )
        response = self.use_case.get_summary(request)
        assert not response.total_results

    def record_request(self) -> None:
        request_handler = self.request_handler_factory.create_request_handler()
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
