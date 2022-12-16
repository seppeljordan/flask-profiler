from flask import render_template

from flask_profiler.presenters.get_summary_presenter import (
    GetSummaryPresenter as Presenter,
)
from flask_profiler.response import HttpResponse


class GetSummaryView:
    def render_view_model(self, view_model: Presenter.ViewModel) -> HttpResponse:
        return HttpResponse(
            content=render_template(
                "summary.html",
                **dict(
                    view_model=view_model,
                )
            )
        )
