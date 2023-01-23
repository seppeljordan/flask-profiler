from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Protocol
from urllib.parse import unquote

from flask import Request


class HttpRequest(Protocol):
    def get_arguments(self) -> Dict[str, str]:
        ...

    def path_arguments(self) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class WrappedRequest:
    request: Request
    flask_path_arguments: Dict[str, Any] = field(default_factory=dict)

    def get_arguments(self) -> Dict[str, str]:
        return {key: unquote(value) for key, value in self.request.args.items()}

    def path_arguments(self) -> Dict[str, Any]:
        return self.flask_path_arguments
