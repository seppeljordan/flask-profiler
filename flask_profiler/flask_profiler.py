# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
import logging
import re
from typing import Any, Callable, Dict, Iterable, List, TypeVar, Union, cast

from flask import Blueprint, Flask
from flask import Response as FlaskResponse
from flask import request
from flask_httpauth import HTTPBasicAuth

from .dependency_injector import DependencyInjector
from .request import WrappedRequest
from .response import HttpResponse
from .storage.base import Measurement, RequestMetadata

ResponseT = Union[str, FlaskResponse]
logger = logging.getLogger("flask-profiler")
auth = HTTPBasicAuth()
Route = TypeVar("Route", bound=Callable[..., ResponseT])


flask_profiler = Blueprint(
    "flask_profiler",
    __name__,
    static_folder="static/",
    static_url_path="/static",
    template_folder="templates",
)


def render_response(response: HttpResponse) -> FlaskResponse:
    return FlaskResponse(
        response=response.content,
        status=response.status_code,
    )


@auth.verify_password
def verify_password(username, password):
    injector = DependencyInjector()
    config = injector.get_configuration()
    if not config.is_basic_auth_enabled:
        return True
    if (
        username == config.basic_auth_username
        and password == config.basic_auth_password
    ):
        return True
    logging.info("flask-profiler authentication failed")
    return False


@flask_profiler.route("/")
@auth.login_required
def summary() -> ResponseT:
    injector = DependencyInjector()
    controller = injector.get_summary_controller()
    response = controller.handle_request(http_request=WrappedRequest(request))
    return render_response(response)


@flask_profiler.route("/details/")
@auth.login_required
def details() -> ResponseT:
    injector = DependencyInjector()
    controller = injector.get_details_controller()
    response = controller.handle_request(http_request=WrappedRequest(request))
    return render_response(response)


@flask_profiler.after_request
def x_robots_tag_header(response) -> FlaskResponse:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


def is_ignored(name: str) -> bool:
    injector = DependencyInjector()
    config = injector.get_configuration()
    for pattern in config.ignore_patterns:
        if re.search(pattern, name):
            return True
    return False


def measure(f: Route, name: str, method: str, context: RequestMetadata) -> Route:
    injector = DependencyInjector()
    clock = injector.get_clock()
    config = injector.get_configuration()
    logger.debug("{0} is being processed.")
    if is_ignored(name):
        logger.debug("{0} is ignored.")
        return f

    @functools.wraps(f)
    def wrapper(*args, **kwargs) -> ResponseT:
        if not config.sampling_function():
            return f(*args, **kwargs)
        started_at = clock.get_epoch()
        try:
            response = f(*args, **kwargs)
        finally:
            stopped_at = clock.get_epoch()
            measurement = Measurement(
                method=method,
                context=context,
                name=name,
                args=sanatize_args(args),
                kwargs=sanatize_kwargs(kwargs),
                startedAt=started_at,
                endedAt=stopped_at,
            )
            logger.debug(str(measurement.serialize_to_json()))
            config.collection.insert(measurement)
        return response

    return cast(Route, wrapper)


def wrap_route(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = RequestMetadata(
            url=request.base_url,
            args=dict(request.args.items()),
            form=dict(request.form.items()),
            headers=dict(request.headers.items()),
            endpoint_name=request.endpoint,
            client_address=request.remote_addr,
        )
        endpoint_name = str(request.url_rule)
        wrapped = measure(f, endpoint_name, request.method, context)
        return wrapped(*args, **kwargs)

    return wrapper


def wrap_all_routes(app):
    """
    wraps all endpoints defined in the given flask app to measure how long time
    each endpoints takes while being executed. This wrapping process is
    supposed not to change endpoint behaviour.
    :param app: Flask application instance
    :return:
    """
    for endpoint, func in app.view_functions.items():
        app.view_functions[endpoint] = wrap_route(func)


def profile():
    """
    http endpoint decorator
    """

    def wrapper(f):
        return wrap_route(f)

    return wrapper


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
    wrap_all_routes(app)
    app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)
    if not config.is_basic_auth_enabled:
        logging.warning("flask-profiler is working without basic auth!")


def sanatize_args(args: Iterable[Any]) -> List[str]:
    return [str(item) for item in args]


def sanatize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, str]:

    for key, value in list(kwargs.items()):
        kwargs[key] = str(value)
    return kwargs
