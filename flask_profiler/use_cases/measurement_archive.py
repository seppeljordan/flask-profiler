from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class MeasurementArchivist(Protocol):
    def record_measurement(self, measurement: Measurement) -> None:
        ...


@dataclass
class Measurement:
    route_name: str
    start_timestamp: datetime
    end_timestamp: datetime
    method: str
