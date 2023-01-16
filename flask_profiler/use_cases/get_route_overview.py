import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from flask_profiler.entities.measurement_archive import MeasurementArchivist


class Interval(enum.Enum):
    daily = enum.auto()
    weekly = enum.auto()
    monthly = enum.auto()


@dataclass
class Request:
    route_name: str
    interval: Interval
    start_time: Optional[datetime]


@dataclass
class IntervalMeasurement:
    timestamp: datetime
    value: float


@dataclass
class Response:
    request: Request
    timeseries: Dict[str, List[IntervalMeasurement]]


@dataclass
class GetRouteOverviewUseCase:
    archivist: MeasurementArchivist

    def get_route_overview(self, request: Request) -> Response:
        timeseries: Dict[str, List[IntervalMeasurement]] = dict()
        measurements = self.archivist.get_records().with_name(request.route_name)
        for summary in measurements.summarize():
            method = summary.method
            timeseries[method] = [IntervalMeasurement(value=0, timestamp=datetime.min)]
        return Response(request=request, timeseries=timeseries)
