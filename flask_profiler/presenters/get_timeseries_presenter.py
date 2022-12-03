from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask_profiler.use_cases.get_timeseries_use_case import (
    GetTimeseriesUseCase as UseCase,
)


class GetTimeseriesPresenter:
    @dataclass
    class ViewModel:
        json_object: Any

    def present_timeseries_as_json_response(
        self, response: UseCase.Response
    ) -> ViewModel:
        if response.interval == UseCase.Interval.daily:
            format_string = "%Y-%m-%d"
        else:
            format_string = "%Y-%m-%d %H"
        return self.ViewModel(
            json_object=dict(
                series={
                    timestamp.strftime(format_string): value
                    for timestamp, value in response.series.items()
                }
            )
        )
