from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask_profiler.clock import Clock

from .measurement_archive import Measurement, MeasurementArchivist
from .request_handler import RequestHandler


@dataclass
class Request:
    request_args: Any
    request_kwargs: Any
    method: str
    route_name: str


@dataclass
class ObserveRequestHandlingUseCase:
    archivist: MeasurementArchivist
    clock: Clock
    request_handler: RequestHandler

    def record_measurement(self, request: Request) -> None:
        start_timestamp = self.clock.utc_now()
        self.request_handler.handle_request(
            args=request.request_args, kwargs=request.request_kwargs
        )
        end_timestamp = self.clock.utc_now()
        self.archivist.record_measurement(
            Measurement(
                route_name=request.route_name,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                method=request.method,
            )
        )
