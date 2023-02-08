from flask import render_template

from flask_profiler.presenters import get_details_presenter as presenter
from flask_profiler.response import HttpResponse


class GetDetailsView:
    def render_view_model(self, view_model: presenter.ViewModel) -> HttpResponse:
        return HttpResponse(
            content=render_template(
                "flask_profiler/details.html",
                **dict(
                    view_model=view_model,
                )
            )
        )
