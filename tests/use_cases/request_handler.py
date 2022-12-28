from dataclasses import dataclass
from datetime import timedelta
from typing import Any, List, Optional

from tests.clock import FakeClock


@dataclass
class HandlerCall:
    args: Any
    kwargs: Any


class FakeRequestHandler:
    def __init__(self, clock: FakeClock, duration: Optional[timedelta] = None) -> None:
        self.calls: List[HandlerCall] = list()
        self.duration = duration
        self.clock = clock

    def handle_request(self, args: Any, kwargs: Any) -> None:
        self.calls.append(HandlerCall(args=args, kwargs=kwargs))
        if self.duration:
            self.clock.advance_clock(self.duration)


@dataclass
class FakeRequestHandlerFactory:
    clock: FakeClock

    def create_request_handler(
        self, duration: Optional[timedelta] = None
    ) -> FakeRequestHandler:
        return FakeRequestHandler(clock=self.clock, duration=duration)
