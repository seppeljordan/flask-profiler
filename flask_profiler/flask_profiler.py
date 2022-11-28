# -*- coding: utf-8 -*-

import functools
import logging
import re
import time
from pprint import pprint as pp
from uuid import UUID

from flask import Blueprint, Flask, current_app, jsonify, request
from flask_httpauth import HTTPBasicAuth

from .configuration import Configuration

logger = logging.getLogger("flask-profiler")
auth = HTTPBasicAuth()


flask_profiler = Blueprint(
    "flask_profiler",
    __name__,
    static_folder="static/dist/",
    static_url_path="/static/dist",
)


@auth.verify_password
def verify_password(username, password):
    config = Configuration(current_app)
    if not config.is_basic_auth_enabled:
        return True

    if (
        username == config.basic_auth_username
        and password == config.basic_auth_password
    ):
        return True
    logging.warning("flask-profiler authentication failed")
    return False


@flask_profiler.route("/")
@auth.login_required
def index():
    return flask_profiler.send_static_file("index.html")


@flask_profiler.route("/api/measurements/")
@auth.login_required
def filterMeasurements():
    config = Configuration(current_app)
    args = dict(request.args.items())
    measurements = config.collection.filter(args)
    return jsonify({"measurements": list(measurements)})


@flask_profiler.route("/api/measurements/grouped")
@auth.login_required
def getMeasurementsSummary():
    config = Configuration(current_app)
    args = dict(request.args.items())
    measurements = config.collection.getSummary(args)
    return jsonify({"measurements": list(measurements)})


@flask_profiler.route("/api/measurements/<measurementId>")
@auth.login_required
def getContext(measurementId):
    config = Configuration(current_app)
    return jsonify(config.collection.get(measurementId))


@flask_profiler.route("/api/measurements/timeseries/")
@auth.login_required
def getRequestsTimeseries():
    config = Configuration(current_app)
    args = dict(request.args.items())
    return jsonify({"series": config.collection.getTimeseries(args)})


@flask_profiler.route("/api/measurements/methodDistribution/")
@auth.login_required
def getMethodDistribution():
    config = Configuration(current_app)
    args = dict(request.args.items())
    return jsonify({"distribution": config.collection.getMethodDistribution(args)})


@flask_profiler.route("/db/dumpDatabase")
@auth.login_required
def dumpDatabase():
    config = Configuration(current_app)
    response = jsonify({"summary": config.collection.getSummary()})
    response.headers["Content-Disposition"] = "attachment; filename=dump.json"
    return response


@flask_profiler.route("/db/deleteDatabase")
@auth.login_required
def deleteDatabase():
    config = Configuration(current_app)
    response = jsonify({"status": config.collection.truncate()})
    return response


@flask_profiler.after_request
def x_robots_tag_header(response):
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


class Measurement:
    """represents an endpoint measurement"""

    DECIMAL_PLACES = 6

    def __init__(self, name, args, kwargs, method, context=None):
        super(Measurement, self).__init__()
        self.context = context
        self.name = name
        self.method = method
        self.args = args
        self.kwargs = kwargs
        self.startedAt = 0
        self.endedAt = 0
        self.elapsed = 0

    def __json__(self):
        return {
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "method": self.method,
            "startedAt": self.startedAt,
            "endedAt": self.endedAt,
            "elapsed": self.elapsed,
            "context": self.context,
        }

    def __str__(self):
        return str(self.__json__())

    def start(self):
        # we use default_timer to get the best clock available.
        # see: http://stackoverflow.com/a/25823885/672798
        self.startedAt = time.time()
        print(self.startedAt)

    def stop(self):
        self.endedAt = time.time()
        print(self.endedAt)
        self.elapsed = round(self.endedAt - self.startedAt, self.DECIMAL_PLACES)


def is_ignored(name: str) -> bool:
    config = Configuration(current_app)
    for pattern in config.ignore_patterns:
        if re.search(pattern, name):
            return True
    return False


def measure(f, name: str, method, context=None):
    logger.debug("{0} is being processed.")
    config = Configuration(current_app)
    if is_ignored(name):
        logger.debug("{0} is ignored.")
        return f

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not config.sampling_function():
            return f(*args, **kwargs)

        measurement = Measurement(name, args, sanatize_kwargs(kwargs), method, context)
        measurement.start()

        try:
            returnVal = f(*args, **kwargs)
        finally:
            measurement.stop()
            if config.verbose:
                pp(measurement.__json__())
            config.collection.insert(measurement.__json__())

        return returnVal

    return wrapper


def wrapHttpEndpoint(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        context = {
            "url": request.base_url,
            "args": dict(request.args.items()),
            "form": dict(request.form.items()),
            "body": request.data.decode("utf-8", "strict"),
            "headers": dict(request.headers.items()),
            "func": request.endpoint,
            "ip": request.remote_addr,
        }
        endpoint_name = str(request.url_rule)
        wrapped = measure(f, endpoint_name, request.method, context)
        return wrapped(*args, **kwargs)

    return wrapper


def wrapAppEndpoints(app):
    """
    wraps all endpoints defined in the given flask app to measure how long time
    each endpoints takes while being executed. This wrapping process is
    supposed not to change endpoint behaviour.
    :param app: Flask application instance
    :return:
    """
    for endpoint, func in app.view_functions.items():
        app.view_functions[endpoint] = wrapHttpEndpoint(func)


def profile(*args, **kwargs):
    """
    http endpoint decorator
    """

    def wrapper(f):
        return wrapHttpEndpoint(f)

    return wrapper


def init_app(app: Flask) -> None:
    """Initialize the flask-profiler package with your flask app.
    Unless flask-profiler is explicityly enabled in the flask config
    this will do nothing.

    Initialization must be one after all routes you want to monitor
    are registered with your app.

    """
    config = Configuration(app)

    if not config.enabled:
        return

    wrapAppEndpoints(app)
    app.register_blueprint(flask_profiler, url_prefix="/" + config.url_prefix)

    if not config.is_basic_auth_enabled:
        logging.warning(" * CAUTION: flask-profiler is working without basic auth!")


def sanatize_kwargs(kwargs):
    for key, value in list(kwargs.items()):
        if isinstance(value, UUID):
            kwargs[key] = str(value)
    return kwargs
