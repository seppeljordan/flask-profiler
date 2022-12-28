from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Protocol
from urllib.parse import unquote

from flask import Request


class HttpRequest(Protocol):
    def get_arguments(self) -> Dict[str, str]:
        ...


@dataclass(frozen=True)
class WrappedRequest:
    request: Request

    @lru_cache(maxsize=1)
    def get_arguments(self) -> Dict[str, str]:
        return {key: unquote(value) for key, value in self.request.args.items()}
