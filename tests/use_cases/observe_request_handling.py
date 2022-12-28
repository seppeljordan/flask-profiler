from dataclasses import dataclass

from flask_profiler.use_cases.observe_request_handling_use_case import (
    ObserveRequestHandlingUseCase,
)
from flask_profiler.use_cases.request_handler import RequestHandler
from tests.clock import FakeClock

from .measurement_archive import FakeMeasurementArchivist


@dataclass
class ObserveRequestHandlingUseCaseFactory:
    archivist: FakeMeasurementArchivist
    clock: FakeClock

    def create_use_case(
        self, request_handler: RequestHandler
    ) -> ObserveRequestHandlingUseCase:
        return ObserveRequestHandlingUseCase(
            clock=self.clock,
            archivist=self.archivist,
            request_handler=request_handler,
        )
