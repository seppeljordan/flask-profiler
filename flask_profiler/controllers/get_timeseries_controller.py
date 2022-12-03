from dataclasses import dataclass
from datetime import datetime

from flask import Request

from flask_profiler.clock import Clock
from flask_profiler.use_cases.get_timeseries_use_case import (
    GetTimeseriesUseCase as UseCase,
)


@dataclass
class GetTimeseriesController:
    clock: Clock

    def parse_request(self, request: Request) -> UseCase.Request:
        current_epoch = self.clock.get_epoch()
        return UseCase.Request(
            interval=UseCase.Interval.daily
            if request.args.get("interval", "hourly") == "daily"
            else UseCase.Interval.hourly,
            started_at=datetime.fromtimestamp(
                float(request.args.get("startedAt", current_epoch - 3600 * 24 * 7))
            ),
            ended_at=datetime.fromtimestamp(
                float(request.args.get("endedAt", current_epoch))
            ),
        )
