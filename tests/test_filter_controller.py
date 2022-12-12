import time
from datetime import datetime
from typing import Any, Dict, Optional
from unittest import TestCase

from flask_profiler.controllers.filter_controller import FilterController
from tests.request import FakeJsonRequest

# This sentinel object is used in default arguments. We don't use None
# since in many cases None would be a valid value that needs to be
# distinguished from not specifying a value.
SENTINEL = object()


class ParseFilterTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.clock = FakeClock()
        self.controller = FilterController(clock=self.clock)

    def test_without_data_the_default_limit_is_100(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.limit == 100

    def test_without_data_the_default_skip_is_0(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.skip == 0

    def test_without_data_the_default_sorting_is_by_endetAt_descending(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.sort[0] == "endedAt"
        assert result.sort[1] == "desc"

    def test_without_data_started_at_is_one_week_before_current_time(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 8))
        result = self.controller.parse_filter(self.create_request())
        assert result.startedAt == datetime(2000, 1, 1)

    def test_without_data_ended_at_is_current_time(self) -> None:
        self.clock.freeze_time(datetime(2000, 1, 8))
        result = self.controller.parse_filter(self.create_request())
        assert result.endedAt == datetime(2000, 1, 8)

    def test_without_data_there_is_no_name_filter(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.name is None

    def test_without_data_there_is_no_method_filter(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.method is None

    def test_without_data_there_is_no_args_filter(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.args is None

    def test_without_data_there_is_no_kwargs_filter(self) -> None:
        result = self.controller.parse_filter(self.create_request())
        assert result.kwargs is None

    def test_with_json_value_for_limit_equal_5_the_limit_is_set_to_5(self) -> None:
        result = self.controller.parse_filter(self.create_request(limit=5))
        assert result.limit == 5

    def test_with_json_value_for_sort_column_equal_to_name_the_query_is_sorted_by_name(
        self,
    ) -> None:
        result = self.controller.parse_filter(self.create_request(sort_column="name"))
        assert result.sort[0] == "name"

    def test_with_json_value_for_sort_column_equal_to_xyz_the_query_is_sorted_by_endedAt(
        self,
    ) -> None:
        result = self.controller.parse_filter(self.create_request(sort_column="xyz"))
        assert result.sort[0] == "endedAt"

    def create_request(
        self, limit: Any = SENTINEL, sort_column: Any = SENTINEL
    ) -> FakeJsonRequest:
        data: Dict[str, Any] = dict()
        if limit is not SENTINEL:
            data["limit"] = limit
        if sort_column is not SENTINEL:
            data["sort_column"] = sort_column
        return FakeJsonRequest(data)


class FakeClock:
    def __init__(self) -> None:
        self.frozen_time: Optional[datetime] = None

    def get_epoch(self) -> float:
        if self.frozen_time:
            return self.frozen_time.timestamp()
        return time.time()

    def freeze_time(self, timestamp: datetime) -> None:
        self.frozen_time = timestamp

    def unfreeze_time(self) -> None:
        self.frozen_time = None
