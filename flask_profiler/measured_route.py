from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Union

from flask import Response as FlaskResponse
from flask import request

from .clock import Clock
from .configuration import Configuration
from .use_cases import observe_request_handling_use_case as use_case
from .use_cases.measurement_archive import MeasurementArchivist

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger("flask-profiler")


class RequestHandler:
    def __init__(self, original_route) -> None:
        self.original_route = original_route
        self.response = None

    def handle_request(self, args: Any, kwargs: Any) -> None:
        self.response = self.original_route(*args, **kwargs)

    def get_response(self):
        return self.response


@dataclass
class MeasuredRoute:
    use_case: use_case.ObserveRequestHandlingUseCase
    request_handler: RequestHandler

    def __call__(self, *args, **kwargs) -> ResponseT:
        self.use_case.record_measurement(
            use_case.Request(
                request_args=args,
                request_kwargs=kwargs,
                route_name=str(request.endpoint),
                method=request.method,
            )
        )
        return self.request_handler.get_response()


@dataclass
class MeasuredRouteFactory:
    clock: Clock
    config: Configuration
    archivist: MeasurementArchivist

    def create_measured_route(
        self, original_route: Callable[..., ResponseT]
    ) -> MeasuredRoute:
        request_handler = RequestHandler(original_route)
        return MeasuredRoute(
            use_case=use_case.ObserveRequestHandlingUseCase(
                request_handler=request_handler,
                clock=self.clock,
                archivist=self.archivist,
            ),
            request_handler=request_handler,
        )
