from __future__ import annotations

import logging

from flask import Blueprint
from flask import Response as FlaskResponse
from flask_httpauth import HTTPBasicAuth

from .dependency_injector import DependencyInjector
from .response import HttpResponse

logger = logging.getLogger(__name__)
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
def verify_password(username: str, password: str) -> bool:
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
    use_case = injector.get_summary_use_case()
    presenter = injector.get_summary_presenter()
    view = injector.get_summary_view()
    uc_request = controller.process_request()
    uc_response = use_case.get_summary(uc_request)
    view_model = presenter.render_summary(uc_response, controller.pagination_context)
    http_response = view.render_view_model(view_model)
    return render_response(http_response)


@flask_profiler.route("/details/")
@auth.login_required
def details() -> FlaskResponse:
    injector = DependencyInjector()
    controller = injector.get_details_controller()
    response = controller.handle_request()
    return render_response(response)


@flask_profiler.route("/route/<route_name>")
@auth.login_required
def route_overview(route_name: str) -> FlaskResponse:
    injector = DependencyInjector()
    controller = injector.get_route_overview_controller()
    response = controller.handle_request()
    return render_response(response)


@flask_profiler.after_request
def x_robots_tag_header(response: FlaskResponse) -> FlaskResponse:
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response
