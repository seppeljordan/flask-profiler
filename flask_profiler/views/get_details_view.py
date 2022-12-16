from flask import render_template

from flask_profiler.presenters.get_details_presenter import (
    GetDetailsPresenter as Presenter,
)
from flask_profiler.response import HttpResponse


class GetDetailsView:
    def render_view_model(self, view_model: Presenter.ViewModel) -> HttpResponse:
        return HttpResponse(
            content=render_template(
                "details.html",
                **dict(
                    view_model=view_model,
                )
            )
        )
