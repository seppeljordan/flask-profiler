from __future__ import annotations

import enum
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional

from flask_profiler.calendar import Calendar
from flask_profiler.entities.measurement_archive import (
    MeasurementArchivist,
    RecordedMeasurements,
)


@dataclass
class GetRouteOverviewUseCase:
    archivist: MeasurementArchivist
    calendar: Calendar

    def get_route_overview(self, request: Request) -> Response:
        timeseries: Dict[str, List[IntervalMeasurement]] = defaultdict(list)
        measurements = (
            self.archivist.get_records()
            .with_name(request.route_name)
            .requested_before(request.end_time)
        )
        if request.start_time:
            measurements = measurements.requested_after(request.start_time)
            interval_start = request.start_time.date()
        else:
            if timestamp := self._get_earliest_measurement(measurements):
                interval_start = timestamp.date()
            else:
                return Response(request=request, timeseries=dict())
        interval = self.calendar.day_interval(
            since=interval_start,
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

    def _get_earliest_measurement(
        self, measurements: RecordedMeasurements
    ) -> Optional[datetime]:
        measurement = measurements.ordered_by_start_time().first()
        if measurement:
            return measurement.start_timestamp
        else:
            return None


@dataclass
class Request:
    route_name: str
    interval: Interval
    start_time: Optional[datetime]
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
