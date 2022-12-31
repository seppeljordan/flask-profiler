from datetime import datetime
from unittest import TestCase

from flask_profiler.entities import measurement_archive as archive
from flask_profiler.sqlite import Sqlite


class SqliteTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = Sqlite(":memory:")
        self.db.create_database()

    def test_after_inserting_a_measurement_there_is_at_least_one_record_present_in_db(
        self,
    ) -> None:
        self.db.record_measurement(
            archive.Measurement(
                route_name="",
                start_timestamp=datetime(2000, 1, 1),
                end_timestamp=datetime(2000, 1, 2),
                method="",
            )
        )
        assert self.db.get_records()

    def test_that_there_are_no_records_present_in_db_before_inserting_a_measurement(
        self,
    ) -> None:
        assert not self.db.get_records()
