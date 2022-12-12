from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from flask_profiler.clock import Clock
from flask_profiler.request import HttpRequest
from flask_profiler.storage.base import FilterQuery


@dataclass
class FilterController:
    clock: Clock

    def parse_filter(self, request: HttpRequest) -> FilterQuery:
        received_json = request.get_content_as_json()
        startedAt = datetime.fromtimestamp(self.clock.get_epoch() - 3600 * 24 * 7)
        endedAt = datetime.fromtimestamp(self.clock.get_epoch())
        query = FilterQuery(
            limit=100,
            skip=0,
            sort=("endedAt", "desc"),
            startedAt=startedAt,
            endedAt=endedAt,
            name=None,
            method=None,
            args=None,
            kwargs=None,
        )
        return query
