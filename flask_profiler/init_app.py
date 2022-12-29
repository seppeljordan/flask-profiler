from __future__ import annotations

import logging
from dataclasses import dataclass

from flask import Flask

from .dependency_injector import DependencyInjector
from .flask_profiler import flask_profiler
from .measured_route import MeasuredRouteFactory

logger = logging.getLogger("flask-profiler")


@dataclass
class RouteWrapper:
    measured_route_factory: MeasuredRouteFactory

    def wrap_all_routes(self, app: Flask):
        """
        wraps all endpoints defined in the given flask app to measure how long time
        each endpoints takes while being executed. This wrapping process is
        supposed not to change endpoint behaviour.
        :param app: Flask application instance
        :return:
        """
        for endpoint, func in app.view_functions.items():
            app.view_functions[
                endpoint
            ] = self.measured_route_factory.create_measured_route(
                original_route=func,
                route_name=endpoint,
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
        measured_route_factory=injector.get_measured_route_factory()
    )
    route_wrapper.wrap_all_routes(app)
    app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)
    if not config.is_basic_auth_enabled:
        logger.warning("flask-profiler is working without basic auth!")
    app.teardown_appcontext(config.cleanup_appcontext)
