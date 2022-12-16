from abc import ABC, abstractmethod

from flask_profiler.request import HttpRequest
from flask_profiler.response import HttpResponse


class Controller(ABC):
    @abstractmethod
    def handle_request(self, http_request: HttpRequest) -> HttpResponse:
        pass
