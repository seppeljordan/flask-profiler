from __future__ import annotations

import logging

from flask import Blueprint
from flask import Response as FlaskResponse
from flask import request
from flask_httpauth import HTTPBasicAuth

from .dependency_injector import DependencyInjector
from .request import WrappedRequest
from .response import HttpResponse

logger = logging.getLogger("flask-profiler")
auth = HTTPBasicAuth()


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
    logger.info("flask-profiler authentication failed")
    return False


@flask_profiler.route("/")
@auth.login_required
def summary() -> FlaskResponse:
    injector = DependencyInjector()
    controller = injector.get_summary_controller()
    response = controller.handle_request(http_request=WrappedRequest(request))
    return render_response(response)


@flask_profiler.route("/details/")
@auth.login_required
def details() -> FlaskResponse:
    injector = DependencyInjector()
    controller = injector.get_details_controller()
    response = controller.handle_request(http_request=WrappedRequest(request))
    return render_response(response)


@flask_profiler.after_request
def x_robots_tag_header(response) -> FlaskResponse:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
