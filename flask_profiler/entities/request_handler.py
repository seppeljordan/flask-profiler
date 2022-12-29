from typing import Any, Protocol


class RequestHandler(Protocol):
    def handle_request(self, args: Any, kwargs: Any) -> Any:
        ...

    def name(self) -> str:
        ...
