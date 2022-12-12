from dataclasses import dataclass
from typing import Any, Optional, Protocol

from flask import Request
from werkzeug.exceptions import BadRequest


class HttpRequest(Protocol):
    def get_content_as_json(self) -> Optional[Any]:
        ...


@dataclass
class WrappedRequest:
    request: Request

    def get_content_as_json(self) -> Any:
        try:
            return self.request.get_json()
        except BadRequest:
            return None
