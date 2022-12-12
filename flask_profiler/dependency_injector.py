from __future__ import annotations

from typing import Optional

from flask import Flask, current_app

from .clock import SystemClock
from .configuration import Configuration
from .controllers.filter_controller import FilterController
from .controllers.get_timeseries_controller import GetTimeseriesController
from .presenters.filtered_presenter import FilteredPresenter
from .presenters.get_timeseries_presenter import GetTimeseriesPresenter
from .presenters.summary_presenter import SummaryPresenter
from .use_cases.get_timeseries_use_case import GetTimeseriesUseCase
from .views import GetRequestsTimeseriesView, GetSummaryDataView


class DependencyInjector:
    def __init__(self, *, app: Optional[Flask] = None) -> None:
        self.app = app or current_app

    def get_clock(self) -> SystemClock:
        return SystemClock()

    def get_filter_controller(self) -> FilterController:
        return FilterController(clock=self.get_clock())

    def get_configuration(self) -> Configuration:
        return Configuration(self.app)

    def get_summary_presenter(self) -> SummaryPresenter:
        return SummaryPresenter()

    def get_filtered_presenter(self) -> FilteredPresenter:
        return FilteredPresenter()

    def get_timeseries_use_case(self) -> GetTimeseriesUseCase:
        return GetTimeseriesUseCase(
            storage=self.get_configuration().collection,
        )

    def get_timeseries_presenter(self) -> GetTimeseriesPresenter:
        return GetTimeseriesPresenter()

    def get_timeseries_controller(self) -> GetTimeseriesController:
        return GetTimeseriesController(clock=self.get_clock())

    def get_requests_timeseries_view(self) -> GetRequestsTimeseriesView:
        return GetRequestsTimeseriesView(
            use_case=self.get_timeseries_use_case(),
            controller=self.get_timeseries_controller(),
            presenter=self.get_timeseries_presenter(),
        )

    def get_summary_data_view(self) -> GetSummaryDataView:
        return GetSummaryDataView(
            controller=self.get_filter_controller(),
            presenter=self.get_summary_presenter(),
            configuration=self.get_configuration(),
        )
