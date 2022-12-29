from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Union

from flask import Response as FlaskResponse
from flask import request

from .clock import Clock
from .configuration import Configuration
from .entities.measurement_archive import MeasurementArchivist
from .use_cases import observe_request_handling_use_case as use_case

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger(__name__)


class RequestHandler:
    def __init__(self, route_name: str, original_route) -> None:
        self.original_route = original_route
        self._name = route_name

    def handle_request(self, args: Any, kwargs: Any) -> Any:
        logger.debug("Executing route %s, args=%s, kwargs=%s", self._name, args, kwargs)
        return self.original_route(*args, **kwargs)

    def name(self) -> str:
        return self._name


@dataclass
class MeasuredRoute:
    use_case: use_case.ObserveRequestHandlingUseCase
    request_handler: RequestHandler

    def __call__(self, *args, **kwargs) -> ResponseT:
        logger.debug("Measuring route %s", self.request_handler.name())
        response = self.use_case.record_measurement(
            use_case.Request(
                request_args=args,
                request_kwargs=kwargs,
                method=request.method,
            )
        )
        logger.debug("Response is %s", response.request_handler_response)
        return response.request_handler_response


@dataclass
class MeasuredRouteFactory:
    clock: Clock
    config: Configuration
    archivist: MeasurementArchivist

    def create_measured_route(
        self, route_name: str, original_route: Callable[..., ResponseT]
    ) -> MeasuredRoute:
        logger.debug("Measuring calls to route %s", route_name)
        request_handler = RequestHandler(
            route_name=route_name, original_route=original_route
        )
        return wraps(original_route)(
            MeasuredRoute(
                use_case=use_case.ObserveRequestHandlingUseCase(
                    request_handler=request_handler,
                    clock=self.clock,
                    archivist=self.archivist,
                ),
                request_handler=request_handler,
            )
        )
