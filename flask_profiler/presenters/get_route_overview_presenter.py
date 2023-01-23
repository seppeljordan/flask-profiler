from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import List

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


@dataclass
class GetRouteOverviewPresenter:
    def render_route_overview(self, response: use_case.Response) -> ViewModel:
        graphs = [
            self._render_graph(
                width=400,
                height=400,
                start_time=response.request.start_time,
                measurements=measurements,
                title=method,
            )
            for method, measurements in response.timeseries.items()
        ]
        return ViewModel(
            headline=f"Route overview for {response.request.route_name}",
            graphs=graphs,
        )

    def _render_graph(
        self,
        *,
        width: float,
        height: float,
        start_time: datetime,
        measurements: List[use_case.IntervalMeasurement],
        title: str,
    ) -> Graph:
        points = [
            Point(
                _x=(measurement.timestamp.date() - start_time.date()).days,
                _y=measurement.value,
            )
            for measurement in measurements
            if measurement.value is not None
        ]
        max_value = max(p._y for p in points)
        unify_points = Conversion.stretch(x=1 / len(measurements), y=1 / max_value)
        normalized_points = [unify_points.transform_point(p) for p in points]
        normalized_lines = [
            Line(
                Point(_x=0, _y=0),
                Point(_x=0, _y=1),
            ),
            Line(
                Point(_x=0, _y=0),
                Point(_x=1, _y=0),
            ),
        ] + [
            Line(p1, p2, color="blue")
            for p1, p2 in zip(normalized_points[:-1], normalized_points[1:])
        ]
        transformation = (
            Conversion.mirror_y()
            .concat(Conversion.translation(y=1))
            .concat(Conversion.stretch(x=width, y=height))
            .concat(Conversion.translation(x=-width / 2, y=-height / 2))
            .concat(Conversion.stretch(x=0.9, y=0.9))
            .concat(Conversion.translation(x=width / 2, y=height / 2))
        )
        transformed_points = [
            transformation.transform_point(p) for p in normalized_points
        ]
        return Graph(
            title=title,
            width=str(width),
            height=str(height),
            points=transformed_points,
            lines=[transformation.transform_line(line) for line in normalized_lines],
        )


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
