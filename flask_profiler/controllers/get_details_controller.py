from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_details_use_case as use_case


@dataclass
class GetDetailsController:
    http_request: HttpRequest
    _pagination_context: Optional[PaginationContext] = None

    def process_request(self) -> use_case.Request:
        form_data = FilterFormData.parse_from_from(self.http_request.get_arguments())
        return use_case.Request(
            limit=self.pagination_context.get_limit(),
            offset=self.pagination_context.get_offset(),
            requested_after=form_data.requested_after,
            requested_before=form_data.requested_before,
            name_filter=form_data.name,
            method_filter=form_data.method,
        )

    @property
    def pagination_context(self) -> PaginationContext:
        if self._pagination_context is None:
            self._pagination_context = PaginationContext.from_http_request(
                self.http_request
            )
        return self._pagination_context
