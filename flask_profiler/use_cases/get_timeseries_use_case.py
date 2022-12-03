from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from flask_profiler.storage.base import BaseStorage


@dataclass
class GetTimeseriesUseCase:
    storage: BaseStorage

    @enum.unique
    class Interval(enum.Enum):
        daily = "daily"
        hourly = "hourly"

    @dataclass
    class Request:
        started_at: datetime
        ended_at: datetime
        interval: GetTimeseriesUseCase.Interval

    @dataclass
    class Response:
        series: Dict[datetime, int]
        interval: GetTimeseriesUseCase.Interval

    def get_timeseries(self, request: Request) -> Response:
        series = self.storage.get_timeseries(
            started_at=request.started_at.timestamp(),
            ended_at=request.ended_at.timestamp(),
            interval=request.interval.value,
        )
        return self.Response(
            interval=request.interval,
            series={
                datetime.fromtimestamp(timestamp): count
                for timestamp, count in series.items()
            },
        )
