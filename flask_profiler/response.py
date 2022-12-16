from dataclasses import dataclass


@dataclass
class HttpResponse:
    status_code: int = 200
    content: str = ""
