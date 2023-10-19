from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from flask_profiler.use_cases import get_route_overview as use_case


@dataclass
class Plot:
    data_points: list[Point]
    x_axis: Line
    y_axis: Line
    x_markings: list[Line]
    y_markings: list[Line]

    @property
    def point_connections(self) -> Iterable[Line]:
        return [
            Line(p1, p2) for p1, p2 in zip(self.data_points[:-1], self.data_points[1:])
        ]

    def transform(self, transformation: Conversion) -> Plot:
        return replace(
            self,
            data_points=[transformation.transform_point(p) for p in self.data_points],
            x_axis=transformation.transform_line(self.x_axis),
            y_axis=transformation.transform_line(self.y_axis),
            x_markings=[
                transformation.transform_line(line) for line in self.x_markings
            ],
            y_markings=[
                transformation.transform_line(line) for line in self.y_markings
            ],
        )


@dataclass
class Point:
    _x: float
    _y: float

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
    plot: Plot


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
        start_time: Optional[datetime],
        end_time: datetime,
        measurements: List[use_case.IntervalMeasurement],
        title: str,
    ) -> Graph:
        start_time = start_time or self._get_earliest_measurement(measurements)
        if start_time is None:
            points = []
        else:
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
        normalize_points = Conversion.stretch(
            x=1 / interval_length_in_days, y=1 / max_value
        )
        normalized_points = [normalize_points.transform_point(p) for p in points]
        plot = Plot(
            data_points=normalized_points,
            x_axis=Line(Point(_x=0, _y=0), Point(_x=1, _y=0)),
            y_axis=Line(Point(_x=0, _y=0), Point(_x=0, _y=1)),
            x_markings=self._generate_markings(max_value, markings_count),
            y_markings=[],
        )
        plot = plot.transform(
            Conversion.mirror_y()
            .concat(Conversion.translation(x=-0.5, y=0.5))  # center graph origin
            .concat(
                Conversion.stretch(x=width * 0.9, y=height * 0.9)
            )  # stretch to fit final dimensions
            .concat(
                Conversion.translation(x=width / 2 + left_border, y=height / 2)
            )  # move origin to left bottom corner
        )
        return Graph(
            title=title,
            width=str(width + left_border),
            height=str(height),
            plot=plot,
        )

    def _get_earliest_measurement(
        self, measurements: List[use_case.IntervalMeasurement]
    ) -> Optional[datetime]:
        try:
            first_measurement, rest_of_measurements = measurements[0], measurements[1:]
        except IndexError:
            return None
        earliest_timestamp = first_measurement.timestamp
        for measurement in rest_of_measurements:
            earliest_timestamp = min(earliest_timestamp, measurement.timestamp)
        return earliest_timestamp

    def _generate_markings(
        self, scale_max_value: float, markings_count: int
    ) -> List[Line]:
        dx = 0.01
        return [
            Line(
                Point(_x=0 - dx, _y=n / markings_count),
                Point(_x=0 + dx, _y=n / markings_count),
                label=f"{n/markings_count * scale_max_value * 1000:.2f} ms",
            )
            for n in range(1, markings_count + 1)
        ]

    def _get_max_scale_value(self, value: float) -> Tuple[float, int]:
        n = 10
        assert value > 0
        power_of_ten = math.ceil(math.log(value, n))
        factor = n**power_of_ten
        value *= n ** (-power_of_ten)
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
