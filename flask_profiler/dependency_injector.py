from __future__ import annotations

from typing import Optional

from flask import Flask, current_app

from .calendar import Calendar
from .clock import SystemClock
from .configuration import Configuration, DeferredArchivist
from .controllers.get_details_controller import GetDetailsController
from .controllers.get_route_overview_controller import GetRouteOverviewController
from .controllers.get_summary_controller import GetSummaryController
from .measured_route import MeasuredRouteFactory
from .presenters.get_details_presenter import GetDetailsPresenter
from .presenters.get_route_overview_presenter import GetRouteOverviewPresenter
from .presenters.get_summary_presenter import GetSummaryPresenter
from .request import WrappedRequest
from .use_cases.get_details_use_case import GetDetailsUseCase
from .use_cases.get_route_overview import GetRouteOverviewUseCase
from .use_cases.get_summary_use_case import GetSummaryUseCase
from .views.get_details_view import GetDetailsView
from .views.get_route_overview_view import GetRouteOverviewView
from .views.get_summary_view import GetSummaryView


class DependencyInjector:
    """Instances of DependencyInjector are only meant to live for
    lifetime of a request.
    """

    def __init__(self, *, app: Optional[Flask] = None) -> None:
        self.app = app or current_app

    def get_clock(self) -> SystemClock:
        return SystemClock()

    def get_configuration(self) -> Configuration:
        return Configuration(self.app)

    def get_summary_use_case(self) -> GetSummaryUseCase:
        return GetSummaryUseCase(archivist=self.get_measurement_archivist())

    def get_summary_controller(self) -> GetSummaryController:
        return GetSummaryController(
            use_case=self.get_summary_use_case(),
            presenter=self.get_summary_presenter(),
            http_request=self.get_http_request(),
        )

    def get_summary_presenter(self) -> GetSummaryPresenter:
        return GetSummaryPresenter(
            view=self.get_summary_view(),
            http_request=self.get_http_request(),
        )

    def get_summary_view(self) -> GetSummaryView:
        return GetSummaryView()

    def get_details_controller(self) -> GetDetailsController:
        return GetDetailsController(
            use_case=self.get_details_use_case(),
            presenter=self.get_details_presenter(),
            http_request=self.get_http_request(),
        )

    def get_details_use_case(self) -> GetDetailsUseCase:
        return GetDetailsUseCase(archivist=self.get_measurement_archivist())

    def get_details_presenter(self) -> GetDetailsPresenter:
        return GetDetailsPresenter(
            view=self.get_details_view(),
            http_request=self.get_http_request(),
        )

    def get_details_view(self) -> GetDetailsView:
        return GetDetailsView()

    def get_measurement_archivist(self) -> DeferredArchivist:
        return DeferredArchivist(self.get_configuration())

    def get_measured_route_factory(self) -> MeasuredRouteFactory:
        return MeasuredRouteFactory(
            clock=self.get_clock(),
            config=self.get_configuration(),
            archivist=self.get_measurement_archivist(),
        )

    def get_route_overview_use_case(self) -> GetRouteOverviewUseCase:
        return GetRouteOverviewUseCase(
            archivist=self.get_measurement_archivist(),
            calendar=self.get_calendar(),
        )

    def get_route_overview_controller(self) -> GetRouteOverviewController:
        return GetRouteOverviewController(
            use_case=self.get_route_overview_use_case(),
            clock=self.get_clock(),
            presenter=self.get_route_overview_presenter(),
            http_request=self.get_http_request(),
        )

    def get_route_overview_presenter(self) -> GetRouteOverviewPresenter:
        return GetRouteOverviewPresenter(
            view=self.get_route_overview_view(),
        )

    def get_calendar(self) -> Calendar:
        return Calendar()

    def get_route_overview_view(self) -> GetRouteOverviewView:
        return GetRouteOverviewView()

    def get_http_request(self) -> WrappedRequest:
        return WrappedRequest()
