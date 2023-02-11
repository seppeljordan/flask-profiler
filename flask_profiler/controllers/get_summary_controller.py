from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from flask_profiler.forms import FilterFormData
from flask_profiler.pagination import PaginationContext
from flask_profiler.request import HttpRequest
from flask_profiler.use_cases import get_summary_use_case as uc


@dataclass
class GetSummaryController:
    http_request: HttpRequest
    _pagination_context: Optional[PaginationContext] = None
    _form_data: Optional[FilterFormData] = None

    def process_request(self) -> uc.Request:
        return uc.Request(
            limit=self.pagination_context.get_limit(),
            offset=self.pagination_context.get_offset(),
            method=self.form_data.method,
            name_filter=self.form_data.name,
            requested_after=self.form_data.requested_after,
            requested_before=self.form_data.requested_before,
        )

    @property
    def form_data(self) -> FilterFormData:
        if self._form_data is None:
            args = self.http_request.get_arguments()
            self._form_data = FilterFormData.parse_from_from(args)
        return self._form_data

    @property
    def pagination_context(self) -> PaginationContext:
        if self._pagination_context is None:
            self._pagination_context = PaginationContext.from_http_request(
                self.http_request
            )
        return self._pagination_context
