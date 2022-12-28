from typing import Dict, Optional, Tuple

from flask_profiler.use_cases import observe_request_handling_use_case as use_case

from .base_test_case import TestCase


class ObserveRequestHandlingUseCaseTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.use_case_factory = (
            self.injector.get_observe_request_handling_use_case_factory()
        )
        self.request_handler_factory = self.injector.get_request_handler_factory()
        self.request_handler = self.request_handler_factory.create_request_handler()
        self.use_case = self.use_case_factory.create_use_case(
            request_handler=self.request_handler
        )

    def test_that_request_handler_is_called_with_proper_args(self) -> None:
        expected_args = (1, 2, 3)
        request = self.create_request(args=expected_args)
        self.use_case.record_measurement(request)
        latest_handler_call = self.request_handler.latest_call()
        assert latest_handler_call
        assert latest_handler_call.args == expected_args

    def test_that_request_handler_is_called_with_proper_kwargs(self) -> None:
        expected_kwargs = dict(a=1, b=2, c=3)
        request = self.create_request(kwargs=expected_kwargs)
        self.use_case.record_measurement(request)
        latest_handler_call = self.request_handler.latest_call()
        assert latest_handler_call
        assert latest_handler_call.kwargs == expected_kwargs

    def create_request(
        self, args: Optional[Tuple] = None, kwargs: Optional[Dict] = None
    ) -> use_case.Request:
        return use_case.Request(
            request_args=args or tuple(),
            request_kwargs=kwargs or dict(),
            method="",
        )
