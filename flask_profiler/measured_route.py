from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Union

from flask import Response as FlaskResponse
from flask import request

from .clock import Clock
from .configuration import Configuration
from .use_cases import record_measurement

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger("flask-profiler")


@dataclass
class MeasuredRoute:
    original_route: Callable[..., ResponseT]
    use_case: record_measurement.RecordMeasurementUseCase
    clock: Clock
    config: Configuration

    def __call__(self, *args, **kwargs) -> ResponseT:
        if self.is_measurement_skipped():
            return self.original_route(*args, **kwargs)
        started_at = self.clock.get_epoch()
        try:
            response = self.original_route(*args, **kwargs)
        finally:
            stopped_at = self.clock.get_epoch()
            self.use_case.record_measurement(
                record_measurement.Request(
                    route_name=str(request.endpoint),
                    start_timestamp=datetime.fromtimestamp(started_at),
                    end_timestamp=datetime.fromtimestamp(stopped_at),
                    method=request.method,
                )
            )
        return response

    def is_measurement_skipped(self) -> bool:
        return self.is_ignored() or not self.config.sampling_function()

    def is_ignored(self) -> bool:
        url_rule = str(request.url_rule)
        for pattern in self.config.ignore_patterns:
            if re.search(pattern, url_rule):
                return True
        return False


@dataclass
class MeasuredRouteFactory:
    use_case: record_measurement.RecordMeasurementUseCase
    clock: Clock
    config: Configuration

    def create_measured_route(
        self, original_route: Callable[..., ResponseT]
    ) -> MeasuredRoute:
        return MeasuredRoute(
            original_route=original_route,
            clock=self.clock,
            config=self.config,
            use_case=self.use_case,
        )
