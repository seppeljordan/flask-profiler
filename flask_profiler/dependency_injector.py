from __future__ import annotations

from typing import Optional

from flask import Flask, current_app

from .clock import SystemClock
from .configuration import Configuration
from .controllers.get_details_controller import GetDetailsController
from .controllers.get_summary_controller import GetSummaryController
from .presenters.get_details_presenter import GetDetailsPresenter
from .presenters.get_summary_presenter import GetSummaryPresenter
from .use_cases.get_details_use_case import GetDetailsUseCase
from .use_cases.get_summary_use_case import GetSummaryUseCase
from .views.get_details_view import GetDetailsView
from .views.get_summary_view import GetSummaryView


class DependencyInjector:
    def __init__(self, *, app: Optional[Flask] = None) -> None:
        self.app = app or current_app

    def get_clock(self) -> SystemClock:
        return SystemClock()

    def get_configuration(self) -> Configuration:
        return Configuration(self.app)

    def get_summary_use_case(self) -> GetSummaryUseCase:
        return GetSummaryUseCase(
            configuration=self.get_configuration(),
        )

    def get_summary_controller(self) -> GetSummaryController:
        return GetSummaryController(
            use_case=self.get_summary_use_case(),
            presenter=self.get_summary_presenter(),
            view=self.get_summary_view(),
        )

    def get_summary_presenter(self) -> GetSummaryPresenter:
        return GetSummaryPresenter()

    def get_summary_view(self) -> GetSummaryView:
        return GetSummaryView()

    def get_details_controller(self) -> GetDetailsController:
        return GetDetailsController(
            use_case=self.get_details_use_case(),
            view=self.get_details_view(),
            presenter=self.get_details_presenter(),
        )

    def get_details_use_case(self) -> GetDetailsUseCase:
        return GetDetailsUseCase(configuration=self.get_configuration())

    def get_details_presenter(self) -> GetDetailsPresenter:
        return GetDetailsPresenter()

    def get_details_view(self) -> GetDetailsView:
        return GetDetailsView()
