from dataclasses import dataclass
from typing import Any, Dict, Protocol
from urllib.parse import unquote

from flask import request


class HttpRequest(Protocol):
    def get_arguments(self) -> Dict[str, str]:
        ...

    def path_arguments(self) -> Dict[str, Any]:
        ...


@dataclass(frozen=True)
class WrappedRequest:
    def get_arguments(self) -> Dict[str, str]:
        return {key: unquote(value) for key, value in request.args.items()}

    def path_arguments(self) -> Dict[str, Any]:
        return request.view_args or dict()
