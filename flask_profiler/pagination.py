from __future__ import annotations

from dataclasses import dataclass

from flask_profiler.request import HttpRequest

PAGE_QUERY_ARGUMENT = "page"


@dataclass
class PaginationContext:
    current_page: int
    page_size: int

    def get_offset(self) -> int:
        return (self.current_page - 1) * self.page_size

    def get_limit(self) -> int:
        return self.page_size

    def get_total_pages_count(self, total_result_count: int) -> int:
        return (total_result_count // self.page_size) + min(
            1, total_result_count % self.page_size
        )

    @classmethod
    def from_http_request(
        cls, request: HttpRequest, page_size: int = 20
    ) -> PaginationContext:
        request_args = request.get_arguments()
        current_page = int(request_args.get(PAGE_QUERY_ARGUMENT, "1"))
        return cls(
            current_page=current_page,
            page_size=page_size,
        )
