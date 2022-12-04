import json
import sqlite3
import threading
from typing import Dict, List

from .base import FilterQuery, Measurement, Record, RequestMetadata, Summary


class Sqlite:
    def __init__(self, sqlite_file: str, table_name: str) -> None:
        self.sqlite_file = sqlite_file
        self.table_name = table_name

        self.connection = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.lock = threading.Lock()
        try:
            self.create_database()
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e):
                raise e

    def create_database(self) -> None:
        with self.lock:
            sql = """
                CREATE TABLE {table_name} (
                    ID Integer PRIMARY KEY AUTOINCREMENT,
                    startedAt REAL,
                    endedAt REAL,
                    elapsed REAL,
                    args TEXT,
                    kwargs TEXT,
                    method TEXT,
                    context TEXT,
                    name TEXT
                );
            """.format(
                table_name=self.table_name,
            )
            self.cursor.execute(sql)

            sql = """
            CREATE INDEX measurement_index ON {table_name}
                (startedAt, endedAt, elapsed, name, method);
            """.format(
                table_name=self.table_name,
            )
            self.cursor.execute(sql)

            self.connection.commit()

    def insert(self, measurement: Measurement) -> None:
        endedAt = measurement.endedAt
        startedAt = measurement.startedAt
        elapsed = measurement.elapsed
        args = json.dumps(list(measurement.args))
        kwargs = json.dumps(measurement.kwargs)
        context = json.dumps(measurement.context.serialize_to_json())
        method = measurement.method
        name = measurement.name

        sql = """INSERT INTO {0} VALUES (
            null, ?, ?, ?, ?,?, ?, ?, ?)""".format(
            self.table_name
        )

        with self.lock:
            self.cursor.execute(
                sql, (startedAt, endedAt, elapsed, args, kwargs, method, context, name)
            )

            self.connection.commit()

    def get_timeseries(
        self, started_at: float, ended_at: float, interval: str
    ) -> Dict[float, int]:
        if interval == "daily":
            interval_seconds = 3600 * 24  # daily
            dateFormat = "%Y-%m-%d"
        else:
            interval_seconds = 3600  # hourly
            dateFormat = "%Y-%m-%d %H"
        with self.lock:
            sql = """SELECT startedAt, count(id) as count
                FROM "{table_name}"
                WHERE endedAt<=:endedAt AND startedAt>=:startedAt
                GROUP BY strftime(:dateFormat, datetime(startedAt, 'unixepoch'))
                ORDER BY startedAt asc
                """.format(
                table_name=self.table_name
            )
            self.cursor.execute(
                sql, dict(endedAt=ended_at, startedAt=started_at, dateFormat=dateFormat)
            )
            rows = self.cursor.fetchall()
        series = {}
        for i in range(int(started_at), int(ended_at) + 1, interval_seconds):
            series[float(i)] = 0
        for row in rows:
            series[row[0]] = row[1]
        return series

    def get_method_distribution(
        self, started_at: float, ended_at: float
    ) -> Dict[str, int]:
        with self.lock:
            sql = """SELECT
                    method, count(id) as count
                FROM "{table_name}"
                where endedAt<=:endedAt AND startedAt>=:startedAt
                group by method
                """.format(
                table_name=self.table_name
            )

            self.cursor.execute(sql, dict(endedAt=ended_at, startedAt=started_at))
            rows = self.cursor.fetchall()
        results = {}
        for row in rows:
            results[row[0]] = row[1]
        return results

    def filter(self, criteria: FilterQuery) -> List[Record]:
        conditions = "WHERE 1=1"

        if criteria.endedAt:
            conditions = conditions + " AND endedAt <= :endedAt"
        if criteria.startedAt:
            conditions = conditions + " AND startedAt >= :startedAt"
        if criteria.elapsed:
            conditions = conditions + " AND elapsed >= :elapsed"
        if criteria.method:
            conditions = conditions + " AND method = :method"
        if criteria.name:
            conditions = conditions + " AND name = :name"

        with self.lock:
            sql = """SELECT * FROM "{table_name}" {conditions}
            order by {sort_field} {sort_direction}
            limit :limit OFFSET :offset """.format(
                table_name=self.table_name,
                conditions=conditions,
                sort_field=criteria.sort[0],
                sort_direction=criteria.sort[1],
            )
            self.cursor.execute(
                sql,
                dict(
                    endedAt=criteria.endedAt.timestamp() if criteria.endedAt else None,
                    startedAt=criteria.startedAt.timestamp()
                    if criteria.startedAt
                    else None,
                    elapsed=criteria.elapsed,
                    method=criteria.method,
                    name=criteria.name,
                    offset=criteria.skip,
                    limit=criteria.limit,
                ),
            )
            rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    def truncate(self) -> bool:
        with self.lock:
            self.cursor.execute("DELETE FROM {0}".format(self.table_name))
            self.connection.commit()
        # Making the api match with mongo collection, this function must return
        # True or False based on success of this delete operation
        return True if self.cursor.rowcount else False

    def _row_to_record(self, row) -> Record:
        raw_context = json.loads(row[7])
        context = RequestMetadata.from_json(raw_context)
        return Record(
            id=row[0],
            startedAt=row[1],
            endedAt=row[2],
            elapsed=row[3],
            args=json.loads(row[4]),
            kwargs=json.loads(row[5]),
            method=row[6],
            context=context,
            name=row[8],
        )

    def get_summary(self, criteria: FilterQuery) -> List[Summary]:
        conditions = "WHERE 1=1 AND"
        if criteria.startedAt:
            conditions = conditions + " startedAt >= :started_at AND"
        if criteria.endedAt:
            conditions = conditions + " endedAt <= :ended_at AND"
        if criteria.elapsed is not None:
            conditions = conditions + " elapsed >= :elapsed AND"
        conditions = conditions.rstrip(" AND")
        with self.lock:
            sql = """SELECT
                    method, name,
                    count(id) as count,
                    min(elapsed) as minElapsed,
                    max(elapsed) as maxElapsed,
                    avg(elapsed) as avgElapsed
                FROM "{table_name}" {conditions}
                group by method, name
                order by {sort_field} {sort_direction}
                """.format(
                table_name=self.table_name,
                conditions=conditions,
                sort_field=criteria.sort[0],
                sort_direction=criteria.sort[1],
            )
            self.cursor.execute(
                sql,
                dict(
                    elapsed=criteria.elapsed,
                    ended_at=criteria.endedAt.timestamp() if criteria.endedAt else None,
                    started_at=criteria.startedAt.timestamp()
                    if criteria.startedAt
                    else None,
                ),
            )
            rows = self.cursor.fetchall()
            return [
                Summary(
                    method=row[0],
                    name=row[1],
                    count=row[2],
                    min_elapsed=row[3],
                    max_elapsed=row[4],
                    avg_elapsed=row[5],
                )
                for row in rows
            ]
