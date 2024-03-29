from datetime import datetime, timedelta, timezone
from typing import Optional
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
        self,
        route_name: str = "test_route_name",
        method: str = "GET",
        start_timestamp: Optional[datetime] = None,
        duration: timedelta = timedelta(days=1),
    ) -> archive.Measurement:
        if start_timestamp is None:
            start_timestamp = datetime(2000, 1, 1)
        end_timestamp = start_timestamp + duration
        return archive.Measurement(
            route_name=route_name,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
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

    @given(expected_route_name=strategies.text())
    @example(expected_route_name="\x00")
    def test_that_summaries_route_name_is_retrieved_exactly_as_it_was_inserted(
        self, expected_route_name: str
    ) -> None:
        id_ = self.db.record_measurement(
            self.create_measurement(route_name=expected_route_name)
        )
        summary = list(self.db.get_records().with_id(id_).summarize())[0]
        assert summary.name == expected_route_name

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
    def test_can_retrieve_measurement_when_filtering_by_containing_route_name(
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

    @given(name=strategies.text())
    def test_can_retrieve_measurement_when_filtering_by_exact_route_name(
        self, name: str
    ) -> None:
        id_ = self.db.record_measurement(self.create_measurement(route_name=name))
        records = self.db.get_records().with_name(name)
        assert records.with_id(id_)

    @given(name=strategies.text(min_size=2))
    def test_substrings_are_not_sufficient_when_filtering_by_exact_route_name(
        self, name: str
    ) -> None:
        id_ = self.db.record_measurement(self.create_measurement(route_name=name))
        records = self.db.get_records().with_name(name[:-1])
        assert not records.with_id(id_)

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

    def test_when_summarizing_measurements_include_timestamp_of_only_measurement_as_first_measurement(
        self,
    ) -> None:
        expected_datetime = datetime(2000, 1, 4, tzinfo=timezone.utc)
        self.db.record_measurement(
            self.create_measurement(start_timestamp=expected_datetime)
        )
        summary = self.db.get_records().summarize()
        route_summary = list(summary)[0]
        assert route_summary.first_measurement == expected_datetime

    def test_when_summarizing_measurements_include_timestamp_of_first_of_two_measurements_as_first_measurement(
        self,
    ) -> None:
        expected_datetime = datetime(2000, 1, 4, tzinfo=timezone.utc)
        self.db.record_measurement(
            self.create_measurement(start_timestamp=expected_datetime)
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 2, 4, tzinfo=timezone.utc)
            )
        )
        summary = self.db.get_records().summarize()
        route_summary = list(summary)[0]
        assert route_summary.first_measurement == expected_datetime

    def test_when_summarizing_measurements_include_timestamp_of_only_measurement_as_last_measurement(
        self,
    ) -> None:
        expected_datetime = datetime(2000, 1, 4, tzinfo=timezone.utc)
        self.db.record_measurement(
            self.create_measurement(start_timestamp=expected_datetime)
        )
        summary = self.db.get_records().summarize()
        route_summary = list(summary)[0]
        assert route_summary.last_measurement == expected_datetime

    def test_when_summarizing_measurements_include_timestamp_of_latter_of_two_measurements_as_last_measurement(
        self,
    ) -> None:
        expected_datetime = datetime(2000, 1, 4, tzinfo=timezone.utc)
        self.db.record_measurement(
            self.create_measurement(start_timestamp=expected_datetime)
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(1999, 1, 4, tzinfo=timezone.utc)
            )
        )
        summary = self.db.get_records().summarize()
        route_summary = list(summary)[0]
        assert route_summary.last_measurement == expected_datetime

    def test_that_summary_can_be_ordered_by_avg_elapsed_in_ascending_order(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(
                route_name="longer measurement", duration=timedelta(days=1)
            ),
        )
        self.db.record_measurement(
            self.create_measurement(
                route_name="shorter measurement", duration=timedelta(seconds=1)
            ),
        )
        summaries = self.db.get_records().summarize()
        assert [summary.name for summary in summaries.sorted_by_avg_elapsed()] == [
            "shorter measurement",
            "longer measurement",
        ]

    def test_that_summary_can_be_ordered_by_avg_elapsed_in_descending_order(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(
                route_name="longer measurement", duration=timedelta(days=1)
            ),
        )
        self.db.record_measurement(
            self.create_measurement(
                route_name="shorter measurement", duration=timedelta(seconds=1)
            ),
        )
        summaries = self.db.get_records().summarize()
        assert [
            summary.name for summary in summaries.sorted_by_avg_elapsed(ascending=False)
        ] == [
            "longer measurement",
            "shorter measurement",
        ]

    def test_that_summary_can_be_ordered_by_name_in_ascending_order(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(route_name="a measurement"),
        )
        self.db.record_measurement(
            self.create_measurement(route_name="b measurement"),
        )
        summaries = self.db.get_records().summarize()
        assert [summary.name for summary in summaries.sorted_by_route_name()] == [
            "a measurement",
            "b measurement",
        ]

    def test_that_summary_can_be_ordered_by_name_in_descending_order(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(route_name="a measurement"),
        )
        self.db.record_measurement(
            self.create_measurement(route_name="b measurement"),
        )
        summaries = self.db.get_records().summarize()
        assert [
            summary.name for summary in summaries.sorted_by_route_name(ascending=False)
        ] == [
            "b measurement",
            "a measurement",
        ]

    def test_that_first_measurement_is_none_if_no_measurements_are_present(
        self,
    ) -> None:
        assert self.db.get_records().first() is None

    def test_that_first_measurement_is_something_if_measurement_is_present(
        self,
    ) -> None:
        self.db.record_measurement(self.create_measurement())
        assert self.db.get_records().first() is not None

    def test_that_first_measurement_is_equal_to_first_measurement_from_list_of_all_measurements(
        self,
    ) -> None:
        for _ in range(100):
            self.db.record_measurement(self.create_measurement())
        assert self.db.get_records().first() == list(self.db.get_records())[0]

    def test_that_measurements_can_be_ordered_by_start_time(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2001, 1, 1, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc)
            )
        )
        measurement = self.db.get_records().ordered_by_start_time().first()
        assert measurement
        assert measurement.start_timestamp.year == 2000

    def test_that_measurements_can_be_ordered_by_start_time_in_descending_order(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2001, 1, 1, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 1, tzinfo=timezone.utc)
            )
        )
        measurement = (
            self.db.get_records().ordered_by_start_time(ascending=False).first()
        )
        assert measurement
        assert measurement.start_timestamp.year == 2001


class SummarizeByIntervalTests(SqliteTests):
    def test_with_empty_db_no_summaries_are_returned(self) -> None:
        summaries = self.db.get_records().summarize_by_interval(
            [datetime(2000, 1, 1), datetime(2100, 1, 1)]
        )
        assert not summaries

    def test_get_two_summaries_if_one_value_is_in_either_of_two_intervals(self) -> None:
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 2, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2050, 1, 2, tzinfo=timezone.utc)
            )
        )
        summaries = self.db.get_records().summarize_by_interval(
            [
                datetime(2000, 1, 1, tzinfo=timezone.utc),
                datetime(2050, 1, 1, tzinfo=timezone.utc),
                datetime(2100, 1, 1, tzinfo=timezone.utc),
            ]
        )
        assert len(summaries) == 2

    def test_that_values_outside_of_interval_are_ignored(self) -> None:
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 2, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2050, 1, 2, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2150, 1, 2, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(1900, 1, 2, tzinfo=timezone.utc)
            )
        )
        summaries = self.db.get_records().summarize_by_interval(
            [
                datetime(2000, 1, 1, tzinfo=timezone.utc),
                datetime(2050, 1, 1, tzinfo=timezone.utc),
                datetime(2100, 1, 1, tzinfo=timezone.utc),
            ]
        )
        assert len(summaries) == 2

    def test_that_first_summary_contains_2_values_if_two_values_are_before_first_interval_break(
        self,
    ) -> None:
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 2, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2000, 1, 3, tzinfo=timezone.utc)
            )
        )
        self.db.record_measurement(
            self.create_measurement(
                start_timestamp=datetime(2050, 1, 2, tzinfo=timezone.utc)
            )
        )
        summary_1, summary_2 = list(
            self.db.get_records().summarize_by_interval(
                [
                    datetime(2000, 1, 1, tzinfo=timezone.utc),
                    datetime(2050, 1, 1, tzinfo=timezone.utc),
                    datetime(2100, 1, 1, tzinfo=timezone.utc),
                ]
            )
        )
        assert summary_1.count == 2

    def test_can_get_values_for_interval_of_length_100(self) -> None:
        start_date = datetime(2000, 1, 1, tzinfo=timezone.utc)
        results = self.db.get_records().summarize_by_interval(
            [start_date + timedelta(days=n) for n in range(100)]
        )
        assert not results
