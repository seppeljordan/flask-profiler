from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime
from typing import List, Optional, Tuple

from flask_profiler.use_cases import get_route_overview as use_case


@dataclass
class Point:
    _x: float
    _y: float
    color: str = "black"

    @property
    def x(self) -> str:
        return str(self._x)

    @property
    def y(self) -> str:
        return str(self._y)


@dataclass
class Line:
    p1: Point
    p2: Point
    color: str = "black"
    label: Optional[str] = None

    @property
    def x1(self) -> str:
        return self.p1.x

    @property
    def y1(self) -> str:
        return self.p1.y

    @property
    def x2(self) -> str:
        return self.p2.x

    @property
    def y2(self) -> str:
        return self.p2.y


@dataclass
class Graph:
    title: str
    width: str
    height: str
    points: List[Point]
    lines: List[Line]


@dataclass
class ViewModel:
    headline: str
    graphs: List[Graph]


class GetRouteOverviewPresenter:
    def present_response(self, response: use_case.Response) -> ViewModel:
        graphs = [
            self._render_graph(
                width=400,
                height=400,
                left_border=100,
                start_time=response.request.start_time,
                end_time=response.request.end_time,
                measurements=measurements,
                title=method,
            )
            for method, measurements in response.timeseries.items()
        ]
        view_model = ViewModel(
            headline=f"Route overview for {response.request.route_name}",
            graphs=graphs,
        )
        return view_model

    def _render_graph(
        self,
        *,
        width: float,
        height: float,
        left_border: float,
        start_time: datetime,
        end_time: datetime,
        measurements: List[use_case.IntervalMeasurement],
        title: str,
    ) -> Graph:
        interval_length_in_days = (end_time.date() - start_time.date()).days
        points = [
            Point(
                _x=(measurement.timestamp.date() - start_time.date()).days,
                _y=measurement.value,
            )
            for measurement in measurements
            if measurement.value is not None
        ]
        max_value, markings_count = self._get_max_scale_value(max(p._y for p in points))
        normalize_values = Conversion.stretch(y=1 / max_value)
        normalize_points = Conversion.stretch(x=1 / interval_length_in_days).concat(
            normalize_values
        )
        normalized_points = [normalize_points.transform_point(p) for p in points]
        axis = [
            Line(
                Point(_x=0, _y=0),
                Point(_x=0, _y=1),
            ),
            Line(
                Point(_x=0, _y=0),
                Point(_x=1, _y=0),
            ),
        ]
        graph_lines = [
            Line(p1, p2, color="blue")
            for p1, p2 in zip(normalized_points[:-1], normalized_points[1:])
        ]
        axis_markings = [
            normalize_values.transform_line(marking)
            for marking in self._generate_markings(max_value, markings_count)
        ]
        normalized_lines = axis + axis_markings + graph_lines
        transformation = (
            Conversion.mirror_y()
            .concat(Conversion.translation(y=1))
            .concat(Conversion.stretch(x=width, y=height))
            .concat(Conversion.translation(x=-width / 2, y=-height / 2))
            .concat(Conversion.stretch(x=0.9, y=0.9))
            .concat(Conversion.translation(x=width / 2, y=height / 2))
            .concat(Conversion.translation(x=left_border))
        )
        return Graph(
            title=title,
            width=str(width + left_border),
            height=str(height),
            points=[transformation.transform_point(p) for p in normalized_points],
            lines=[transformation.transform_line(line) for line in normalized_lines],
        )

    def _generate_markings(
        self, scale_max_value: float, markings_count: int
    ) -> List[Line]:
        dx = 0.01
        return [
            Line(
                Point(_x=0 - dx, _y=n / markings_count * scale_max_value),
                Point(_x=0 + dx, _y=n / markings_count * scale_max_value),
                label=f"{n/markings_count * scale_max_value * 1000:.2f} ms",
            )
            for n in range(1, markings_count + 1)
        ]

    def _get_max_scale_value(self, value: float) -> Tuple[float, int]:
        factor = 1.0
        while value < 1:
            factor *= 0.1
            value *= 10
        while value > 10:
            factor *= 10
            value *= 0.1
        return factor * math.ceil(value), math.ceil(value)


@dataclass
class Conversion:
    rows: List[List[float]]

    @classmethod
    def stretch(cls, *, x: float = 1, y: float = 1) -> Conversion:
        return cls(
            [
                [x, 0, 0],
                [0, y, 0],
                [0, 0, 1],
            ]
        )

    @classmethod
    def translation(cls, *, x: float = 0, y: float = 0) -> Conversion:
        return cls(
            [
                [1, 0, x],
                [0, 1, y],
                [0, 0, 1],
            ]
        )

    @classmethod
    def mirror_y(cls) -> Conversion:
        return cls(
            [
                [1, 0, 0],
                [0, -1, 0],
                [0, 0, 1],
            ]
        )

    def transform_point(self, p: Point) -> Point:
        return replace(
            p,
            _x=p._x * self[0][0] + p._y * self[0][1] + 1 * self[0][2],
            _y=p._x * self[1][0] + p._y * self[1][1] + 1 * self[1][2],
        )

    def transform_line(self, line: Line) -> Line:
        return replace(
            line,
            p1=self.transform_point(line.p1),
            p2=self.transform_point(line.p2),
        )

    def concat(self, other: Conversion) -> Conversion:
        return Conversion(
            rows=[
                [sum(other[x][j] * self[j][y] for j in range(3)) for y in range(3)]
                for x in range(3)
            ],
        )

    def __getitem__(self, x: int) -> List[float]:
        return self.rows[x]
