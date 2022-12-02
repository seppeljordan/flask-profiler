from unittest import TestCase

from flask_profiler.storage.base import RequestMetadata


class TestDeserialization(TestCase):
    def test_can_construct_object_from_exactly_the_right_fields(self) -> None:
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            endpoint_name="",
            client_address="",
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata

    def test_can_construct_object_with_addional_fields(self) -> None:
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            endpoint_name="",
            client_address="",
            body="",
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata

    def test_can_construct_object_when_there_is_func_but_not_endpoint_name(
        self,
    ) -> None:
        expected_name = "testname"
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            func=expected_name,
            client_address="",
            body="",
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata.endpoint_name == expected_name

    def test_can_construct_object_when_there_is_no_client_address_but_ip(
        self,
    ) -> None:
        expected_ip = "1.2.3.4"
        data = dict(
            url="test",
            args={},
            form={},
            headers={},
            endpoint_name="",
            ip=expected_ip,
            body="",
        )
        metadata = RequestMetadata.from_json(data)
        assert metadata.client_address == expected_ip
