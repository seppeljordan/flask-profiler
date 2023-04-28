from __future__ import annotations

import enum
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

from flask_profiler.calendar import Calendar
from flask_profiler.entities.measurement_archive import MeasurementArchivist


@dataclass
class GetRouteOverviewUseCase:
    archivist: MeasurementArchivist
    calendar: Calendar

    def get_route_overview(self, request: Request) -> Response:
        timeseries: Dict[str, List[IntervalMeasurement]] = defaultdict(list)
        measurements = (
            self.archivist.get_records()
            .with_name(request.route_name)
            .requested_after(request.start_time)
            .requested_before(request.end_time)
        )
        interval = self.calendar.day_interval(
            since=request.start_time.date(),
            until=request.end_time.date() + timedelta(days=1),
        )
        for summary in measurements.summarize_by_interval(
            [_midnight(d) for d in interval]
        ):
            timeseries[summary.method].append(
                IntervalMeasurement(
                    value=summary.avg_elapsed,
                    timestamp=summary.first_measurement,
                )
            )
        return Response(request=request, timeseries=timeseries)


@dataclass
class Request:
    route_name: str
    interval: Interval
    start_time: datetime
    end_time: datetime


@dataclass
class Response:
    request: Request
    timeseries: Dict[str, List[IntervalMeasurement]]


class Interval(enum.Enum):
    daily = enum.auto()


@dataclass
class IntervalMeasurement:
    timestamp: datetime
    value: Optional[float]


def _midnight(d: date) -> datetime:
    return datetime.combine(d, time(), tzinfo=timezone.utc)
