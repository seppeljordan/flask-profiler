from datetime import date
from unittest import TestCase

from hypothesis import given, strategies

from flask_profiler import calendar


class CalendarDaysTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.calendar = calendar.Calendar()

    def test_that_the_correct_number_of_days_is_caluclated_between_two_days(
        self,
    ) -> None:
        samples = [
            (date(2000, 1, 1), date(1999, 12, 31), 0),
            (date(2000, 1, 1), date(2000, 1, 2), 1),
            (date(2000, 1, 1), date(2000, 1, 3), 2),
        ]
        for since, until, expected_days in samples:
            with self.subTest():
                assert (
                    len(self.calendar.day_interval(since=since, until=until))
                    == expected_days
                )

    @given(since=strategies.dates())
    def test_that_the_start_date_is_included_in_the_interval(self, since: date) -> None:
        assert since in self.calendar.day_interval(since=since, until=date.max)

    @given(until=strategies.dates())
    def test_that_the_end_date_is_not_included_in_the_interval(
        self, until: date
    ) -> None:
        assert until not in self.calendar.day_interval(since=date.min, until=until)

    @given(
        since=strategies.dates(), until=strategies.dates(), element=strategies.dates()
    )
    def test_date_considered_in_interval_if_greater_or_equal_then_since_and_lower_then_until(
        self, since: date, until: date, element: date
    ) -> None:
        interval = self.calendar.day_interval(since=since, until=until)
        assert (element in interval) == (since <= element and element < until)

    def test_that_2nd_of_jan_is_included_in_interval_from_1st_to_3rd_of_jan(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 1), until=date(2000, 1, 3)
        )
        assert date(2000, 1, 2) in list(interval)

    def test_that_7th_of_jan_is_included_in_interval_from_6th_to_9th_of_jan(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 6), until=date(2000, 1, 9)
        )
        assert date(2000, 1, 7) in list(interval)

    def test_that_7th_of_jan_is_included_in_interval_from_5th_to_9th_of_jan(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 5), until=date(2000, 1, 9)
        )
        assert date(2000, 1, 7) in list(interval)

    def test_that_8th_of_jan_is_included_in_interval_from_1st_to_9th_of_jan(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 1), until=date(2000, 1, 9)
        )
        assert date(2000, 1, 8) in list(interval)

    def test_that_8th_of_jan_is_not_included_in_interval_from_1st_to_8th_of_jan(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 1), until=date(2000, 1, 8)
        )
        assert date(2000, 1, 8) not in list(interval)

    def test_that_8th_of_jan_2000_is_included_in_interval_from_min_to_max(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date.min,
            until=date.max,
        )
        assert date(2000, 1, 8) in list(interval)

    def test_that_8th_of_oct_is_included_in_interval_from_1st_of_jan_to_9th_of_oct(
        self,
    ) -> None:
        interval = self.calendar.day_interval(
            since=date(2000, 1, 1), until=date(2000, 10, 9)
        )
        assert date(2000, 10, 8) in list(interval)
