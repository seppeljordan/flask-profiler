from dataclasses import dataclass
from datetime import timedelta
from typing import Any, List, Optional

from tests.clock import FakeClock


@dataclass
class HandlerCall:
    args: Any
    kwargs: Any


class FakeRequestHandler:
    def __init__(
        self, clock: FakeClock, handler_name: str, duration: Optional[timedelta] = None
    ) -> None:
        self._calls: List[HandlerCall] = list()
        self.duration = duration
        self.clock = clock
        self.handler_name = handler_name

    def handle_request(self, args: Any, kwargs: Any) -> None:
        self._calls.append(HandlerCall(args=args, kwargs=kwargs))
        if self.duration:
            self.clock.advance_clock(self.duration)

    def name(self) -> str:
        return self.handler_name

    def latest_call(self) -> Optional[HandlerCall]:
        if self._calls:
            return self._calls[-1]
        return None


@dataclass
class FakeRequestHandlerFactory:
    clock: FakeClock

    def create_request_handler(
        self,
        duration: Optional[timedelta] = None,
        handler_name: str = "test handler name",
    ) -> FakeRequestHandler:
        return FakeRequestHandler(
            clock=self.clock, duration=duration, handler_name=handler_name
        )
