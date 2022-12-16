from dataclasses import dataclass
from typing import Dict, Protocol
from urllib.parse import unquote

from flask import Request


class HttpRequest(Protocol):
    def get_arguments(self) -> Dict[str, str]:
        pass


@dataclass
class WrappedRequest:
    request: Request

    def get_arguments(self) -> Dict[str, str]:
        return {key: unquote(value) for key, value in self.request.args.items()}
