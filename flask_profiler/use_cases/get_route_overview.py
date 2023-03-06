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


class Interval(enum.Enum):
    daily = enum.auto()


@dataclass
class Request:
    route_name: str
    interval: Interval
    start_time: datetime
    end_time: datetime


@dataclass
class IntervalMeasurement:
    timestamp: datetime
    value: Optional[float]


@dataclass
class Response:
    request: Request
    timeseries: Dict[str, List[IntervalMeasurement]]


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
            .requested_after(request.start_time)
        )
        interval = self.calendar.day_interval(
            since=request.start_time.date(),
            until=request.end_time.date() + timedelta(days=1),
        )
        for summary in measurements.summarize_by_interval(
            list(
                map(
                    lambda d: datetime.combine(d, time(), tzinfo=timezone.utc), interval
                )
            )
        ):
            timeseries[summary.method].append(
                IntervalMeasurement(
                    value=summary.avg_elapsed,
                    timestamp=summary.first_measurement,
                )
            )
        return Response(request=request, timeseries=timeseries)

    def _get_daily_measurement(
        self, measurements: RecordedMeasurements, day: date, method: str
    ) -> IntervalMeasurement:
        daily_measurements = (
            measurements.with_method(method)
            .requested_after(datetime.combine(day, time(), tzinfo=timezone.utc))
            .requested_before(
                datetime.combine(day + timedelta(days=1), time(), tzinfo=timezone.utc)
            )
        )
        try:
            measurement = next(iter(daily_measurements.summarize()))
        except StopIteration:
            measurement = None
        return IntervalMeasurement(
            value=measurement.avg_elapsed if measurement else None,
            timestamp=datetime.combine(day, time()),
        )
