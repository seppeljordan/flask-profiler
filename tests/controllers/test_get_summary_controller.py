from copy import copy
from dataclasses import dataclass, field
from typing import Any, Dict
from unittest import TestCase

from flask_profiler.controllers.get_summary_controller import GetSummaryController
from flask_profiler.use_cases import get_summary_use_case as uc


class GetSummaryControllerTests(TestCase):
    def test_that_by_default_no_sorting_field_is_detected(self) -> None:
        controller = GetSummaryController(
            http_request=FakeHttpRequest(),
        )
        request = controller.process_request()
        assert request.sorting_field == uc.SortingField.none

    def test_that_by_default_ascending_sorting_order_is_assumed(self) -> None:
        controller = GetSummaryController(
            http_request=FakeHttpRequest(),
        )
        request = controller.process_request()
        assert request.sorting_order == uc.SortingOrder.ascending

    def test_that_sorted_by_field_is_parsed_properly(self) -> None:
        examples = [
            ("-average_time", uc.SortingField.average_time, uc.SortingOrder.descending),
            ("+average_time", uc.SortingField.average_time, uc.SortingOrder.ascending),
            ("average_time", uc.SortingField.average_time, uc.SortingOrder.ascending),
            ("-route_name", uc.SortingField.route_name, uc.SortingOrder.descending),
            ("+route_name", uc.SortingField.route_name, uc.SortingOrder.ascending),
            ("route_name", uc.SortingField.route_name, uc.SortingOrder.ascending),
        ]
        for sorted_by_string, expected_field, expected_order in examples:
            controller = GetSummaryController(
                http_request=FakeHttpRequest(
                    arguments=dict(sorted_by=sorted_by_string)
                ),
            )
            request = controller.process_request()
            assert request.sorting_field == expected_field
            assert request.sorting_order == expected_order


@dataclass
class FakeHttpRequest:
    arguments: Dict[str, str] = field(default_factory=dict)
    path: Dict[str, Any] = field(default_factory=dict)

    def get_arguments(self) -> Dict[str, str]:
        return copy(self.arguments)

    def path_arguments(self) -> Dict[str, Any]:
        return copy(self.path)
