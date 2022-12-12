from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from flask import Request

from flask_profiler.clock import Clock
from flask_profiler.storage.base import FilterQuery


@dataclass
class FilterController:
    clock: Clock

    def parse_filter(self, request: Request) -> FilterQuery:
        arguments = dict(request.args.items())
        limit = int(arguments.get("limit", 100))
        skip = int(arguments.get("skip", 0))
        sort = tuple(str(arguments.get("sort", "endedAt,desc")).split(","))
        sort = (
            sort[0],
            sort[1],
        )
        startedAt = datetime.fromtimestamp(
            float(arguments.get("startedAt", self.clock.get_epoch() - 3600 * 24 * 7))
        )
        endedAt = datetime.fromtimestamp(
            float(arguments.get("endedAt", self.clock.get_epoch()))
        )
        name = arguments.get("name", None)
        method = arguments.get("method", None)
        args = arguments.get("args", None)
        kwargs = arguments.get("kwargs", None)
        query = FilterQuery(
            limit=limit,
            skip=skip,
            sort=sort,
            startedAt=startedAt,
            endedAt=endedAt,
            name=name,
            method=method,
            args=args,
            kwargs=kwargs,
        )
        return query
