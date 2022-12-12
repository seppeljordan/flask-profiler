from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from flask_profiler.clock import Clock
from flask_profiler.request import HttpRequest
from flask_profiler.storage.base import FilterQuery

ALLOWED_SORT_COLUMN = {
    "name",
}


@dataclass
class FilterController:
    clock: Clock

    def parse_filter(self, request: HttpRequest) -> FilterQuery:
        received_json = request.get_content_as_json() or dict()
        startedAt = datetime.fromtimestamp(self.clock.get_epoch() - 3600 * 24 * 7)
        endedAt = datetime.fromtimestamp(self.clock.get_epoch())
        limit = received_json.get("limit", 100)
        sort_column = received_json.get("sort_column", "endedAt")
        if sort_column not in ALLOWED_SORT_COLUMN:
            sort_column = "endedAt"
        query = FilterQuery(
            limit=limit,
            skip=0,
            sort=(sort_column, "desc"),
            startedAt=startedAt,
            endedAt=endedAt,
            name=None,
            method=None,
            args=None,
            kwargs=None,
        )
        return query
