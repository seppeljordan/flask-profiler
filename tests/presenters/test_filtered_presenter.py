from typing import Dict, List, Optional
from unittest import TestCase

from flask_profiler.presenters.filtered_presenter import FilteredPresenter
from flask_profiler.storage.base import Record, RequestMetadata


class PresenterTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.presenter = FilteredPresenter()

    def test_get_empty_list_of_measurements_when_no_measurements_are_to_be_presented(
        self,
    ) -> None:
        view_model = self.presenter.present_filtered_measurements([])
        assert not view_model["measurements"]

    def test_that_one_measurement_is_presented_when_one_is_given(self) -> None:
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record()]
        )
        assert len(view_model["measurements"]) == 1

    def test_that_id_field_is_filled_with_proper_id(self) -> None:
        expected_id = 123
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(id_=expected_id)]
        )
        assert view_model["measurements"][0]["id"] == expected_id

    def test_that_started_at_field_is_filled_properly(self) -> None:
        expected_timestamp = 6432.2
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(started_at=expected_timestamp)]
        )
        assert view_model["measurements"][0]["startedAt"] == expected_timestamp

    def test_that_ended_at_is_filled_with_proper_value(self) -> None:
        expected_timestamp = 64345.21
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(ended_at=expected_timestamp)]
        )
        assert view_model["measurements"][0]["endedAt"] == expected_timestamp

    def test_that_elapsed_is_filled_with_proper_value(self) -> None:
        expected_duration = 123.213
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(elapsed=expected_duration)]
        )
        assert view_model["measurements"][0]["elapsed"] == expected_duration

    def test_that_args_is_filled_with_proper_value(self) -> None:
        expected_args = ["1", "2", "3"]
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(args=expected_args)]
        )
        assert view_model["measurements"][0]["args"] == expected_args

    def test_that_kwargs_is_filled_with_proper_value(self) -> None:
        expected_kwargs = {
            "a": "b",
            "c": "d",
        }
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(kwargs=expected_kwargs)]
        )
        assert view_model["measurements"][0]["kwargs"] == expected_kwargs

    def test_that_method_is_filled_with_proper_value(self) -> None:
        expected_method = "DELETE"
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(method=expected_method)]
        )
        assert view_model["measurements"][0]["method"] == expected_method

    def test_that_context_is_filled_properly(self) -> None:
        expected_request_metadata = self.create_request_metadata(url="test path")
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(request_metadata=expected_request_metadata)]
        )
        assert (
            view_model["measurements"][0]["context"]
            == expected_request_metadata.serialize_to_json()
        )

    def test_that_name_is_filled_properly(self) -> None:
        expected_name = "testname 123"
        view_model = self.presenter.present_filtered_measurements(
            [self.create_record(name=expected_name)]
        )
        assert view_model["measurements"][0]["name"] == expected_name

    def create_record(
        self,
        id_: int = 1,
        started_at: float = 0.0,
        ended_at: float = 1.0,
        elapsed: float = 1.0,
        args: Optional[List[str]] = None,
        kwargs: Optional[Dict[str, str]] = None,
        method: str = "GET",
        request_metadata: Optional[RequestMetadata] = None,
        name: str = "testname",
    ) -> Record:
        if args is None:
            args = []
        if kwargs is None:
            kwargs = dict()
        return Record(
            id=id_,
            name=name,
            startedAt=started_at,
            endedAt=ended_at,
            elapsed=elapsed,
            args=args,
            kwargs=kwargs,
            method=method,
            context=request_metadata or self.create_request_metadata(),
        )

    def create_request_metadata(self, url: str = "abc") -> RequestMetadata:
        return RequestMetadata(
            url=url,
            args=dict(),
            form=dict(),
            headers=dict(),
            endpoint_name="",
            client_address="",
        )
