from datetime import datetime
from unittest import TestCase

from hypothesis import example, given, strategies

from flask_profiler.entities import measurement_archive as archive
from flask_profiler.sqlite import Sqlite


class SqliteTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.db = Sqlite(":memory:")
        self.db.create_database()

    def create_measurement(
        self, route_name: str = "test_route_name", method: str = "GET"
    ) -> archive.Measurement:
        return archive.Measurement(
            route_name=route_name,
            start_timestamp=datetime(2000, 1, 1),
            end_timestamp=datetime(2000, 1, 2),
            method=method,
        )


class RecordMeasurementTests(SqliteTests):
    def test_that_retrieved_id_is_equal_to_id_in_newly_created_measurement(
        self,
    ) -> None:
        id_ = self.db.record_measurement(self.create_measurement())
        measurement = list(self.db.get_records().with_id(id_))[0]
        assert measurement.id == id_

    @given(expected_route_name=strategies.text())
    @example(expected_route_name="\x00")
    def test_that_records_route_name_is_retrieved_exactly_as_it_was_inserted(
        self, expected_route_name: str
    ) -> None:
        id_ = self.db.record_measurement(
            self.create_measurement(route_name=expected_route_name)
        )
        measurement = list(self.db.get_records().with_id(id_))[0]
        assert measurement.name == expected_route_name

    @given(method=strategies.text())
    @example(method="\x00")
    def test_that_method_is_retrieved_exactly_as_measured(self, method: str) -> None:
        id_ = self.db.record_measurement(self.create_measurement(method=method))
        measurement = list(self.db.get_records().with_id(id_))[0]
        assert measurement.method == method


class GetRecordsTests(SqliteTests):
    def test_after_inserting_a_measurement_there_is_at_least_one_record_present_in_db(
        self,
    ) -> None:
        self.db.record_measurement(self.create_measurement())
        assert self.db.get_records()

    def test_that_there_are_no_records_present_in_db_before_inserting_a_measurement(
        self,
    ) -> None:
        assert not self.db.get_records()

    @given(route_name=strategies.text())
    @example(route_name=":")
    def test_can_retrieve_measurement_when_filtering_by_exact_route_name(
        self, route_name: str
    ) -> None:
        id_ = self.db.record_measurement(self.create_measurement(route_name=route_name))
        records = self.db.get_records().with_name_containing(route_name)
        assert records.with_id(id_)

    @given(method=strategies.text())
    @example(method=":")
    def test_can_retrieve_measurement_when_filtering_by_exact_method_name(
        self, method: str
    ) -> None:
        id_ = self.db.record_measurement(self.create_measurement(method=method))
        records = self.db.get_records().with_method(method)
        assert records.with_id(id_)

    def test_can_filter_measurements_by_id(self) -> None:
        id_ = self.db.record_measurement(self.create_measurement())
        records = self.db.get_records()
        assert records.with_id(id_)

    def test_when_filtering_by_id_only_retrieve_elements_with_requested_id(
        self,
    ) -> None:
        self.db.record_measurement(self.create_measurement())
        id_ = self.db.record_measurement(self.create_measurement())
        records = self.db.get_records()
        assert all(record.id == id_ for record in records.with_id(id_))
