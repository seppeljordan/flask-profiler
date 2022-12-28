from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, TypeVar, Union

from flask import Flask
from flask import Response as FlaskResponse
from flask import request

from .clock import Clock
from .configuration import Configuration
from .dependency_injector import DependencyInjector
from .flask_profiler import flask_profiler
from .use_cases import record_measurement

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger("flask-profiler")
Route = TypeVar("Route", bound=Callable[..., ResponseT])


@dataclass
class MeasuredRoute:
    original_route: Callable[..., ResponseT]
    use_case: record_measurement.RecordMeasurementUseCase
    clock: Clock
    config: Configuration

    def __call__(self, *args, **kwargs):
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

    def is_measurement_skipped(self):
        return self.is_ignored() or not self.config.sampling_function()

    def is_ignored(self) -> bool:
        url_rule = str(request.url_rule)
        for pattern in self.config.ignore_patterns:
            if re.search(pattern, url_rule):
                return True
        return False


@dataclass
class RouteWrapper:
    clock: Clock
    use_case: record_measurement.RecordMeasurementUseCase
    config: Configuration

    def wrap_all_routes(self, app):
        """
        wraps all endpoints defined in the given flask app to measure how long time
        each endpoints takes while being executed. This wrapping process is
        supposed not to change endpoint behaviour.
        :param app: Flask application instance
        :return:
        """
        for endpoint, func in app.view_functions.items():
            app.view_functions[endpoint] = MeasuredRoute(
                original_route=func,
                clock=self.clock,
                use_case=self.use_case,
                config=self.config,
            )


def init_app(app: Flask) -> None:
    """Initialize the flask-profiler package with your flask app.
    Unless flask-profiler is explicityly enabled in the flask config
    this will do nothing.

    Initialization must be one after all routes you want to monitor
    are registered with your app.
    """
    injector = DependencyInjector(app=app)
    config = injector.get_configuration()
    if not config.enabled:
        return
    route_wrapper = RouteWrapper(
        config=config,
        use_case=injector.get_record_measurement_use_case(),
        clock=injector.get_clock(),
    )
    route_wrapper.wrap_all_routes(app)
    app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)
    if not config.is_basic_auth_enabled:
        logger.warning("flask-profiler is working without basic auth!")
