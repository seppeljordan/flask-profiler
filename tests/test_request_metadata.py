from unittest import TestCase

from flask_profiler.storage.base import RequestMetadata


class TestDeserialization(TestCase):
    def test_can_construct_object_from_exactly_the_right_fields(self) -> None:
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            endpoint_name={},
            client_address={},
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata

    def test_can_construct_object_with_addional_fields(self) -> None:
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            endpoint_name={},
            client_address={},
            body="",
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata
