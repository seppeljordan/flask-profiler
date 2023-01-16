import unittest
from functools import lru_cache

from flask_profiler.use_cases.get_details_use_case import GetDetailsUseCase
from flask_profiler.use_cases.get_route_overview import GetRouteOverviewUseCase
from flask_profiler.use_cases.get_summary_use_case import GetSummaryUseCase
from tests.clock import FakeClock

from .measurement_archive import FakeMeasurementArchivist
from .observe_request_handling import ObserveRequestHandlingUseCaseFactory
from .request_handler import FakeRequestHandlerFactory


class TestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.injector = DependencyInjector()


singleton = lru_cache(1)


class DependencyInjector:
    @singleton
    def get_measurement_archivist(self) -> FakeMeasurementArchivist:
        return FakeMeasurementArchivist()

    @singleton
    def get_clock(self) -> FakeClock:
        return FakeClock()

    def get_details_use_case(self) -> GetDetailsUseCase:
        return GetDetailsUseCase(archivist=self.get_measurement_archivist())

    def get_summary_use_case(self) -> GetSummaryUseCase:
        return GetSummaryUseCase(archivist=self.get_measurement_archivist())

    def get_request_handler_factory(self) -> FakeRequestHandlerFactory:
        return FakeRequestHandlerFactory(clock=self.get_clock())

    def get_observe_request_handling_use_case_factory(
        self,
    ) -> ObserveRequestHandlingUseCaseFactory:
        return ObserveRequestHandlingUseCaseFactory(
            clock=self.get_clock(),
            archivist=self.get_measurement_archivist(),
        )

    def get_route_overview_use_case(self) -> GetRouteOverviewUseCase:
        return GetRouteOverviewUseCase(archivist=self.get_measurement_archivist())
