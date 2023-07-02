from dataclasses import dataclass
from logging import getLogger

from flask import Flask

from .dependency_injector import DependencyInjector
from .flask_profiler import flask_profiler
from .measured_route import MeasuredRouteFactory

logger = getLogger("flask-profiler")


@dataclass
class RouteWrapper:
    measured_route_factory: MeasuredRouteFactory

    def wrap_all_routes(self, app: Flask) -> None:
        """This function wraps all the endpoints defined in the
        provided Flask app in order to measure the execution time of
        each endpoint. The purpose of this wrapping process is to
        monitor the time taken by each endpoint without affecting
        their original behavior.
        """
        for endpoint, func in app.view_functions.items():
            app.view_functions[
                endpoint
            ] = self.measured_route_factory.create_measured_route(
                original_route=func,
                route_name=endpoint,
            )


def init_app(app: Flask) -> None:
    """This function initializes the flask-profiler package with your
    Flask app. If flask-profiler is not explicitly enabled in the
    Flask configuration, this function will have no effect.

    It's important to call this function after registering all the
    routes that you want to monitor with your app.
    """
    injector = DependencyInjector(app=app)
    config = injector.get_configuration()
    if not config.enabled:
        return
    route_wrapper = RouteWrapper(
        measured_route_factory=injector.get_measured_route_factory()
    )
    with app.app_context():
        config.collection.create_database()
    if config.profile_self:
        app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)
        route_wrapper.wrap_all_routes(app)
    else:
        route_wrapper.wrap_all_routes(app)
        app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)
    if not config.is_basic_auth_enabled:
        logger.warning("flask-profiler is working without basic auth!")
    app.teardown_appcontext(config.cleanup_appcontext)
