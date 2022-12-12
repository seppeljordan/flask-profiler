# -*- coding: utf-8 -*-
import unittest
from uuid import uuid4

from flask import Request
from flask_testing import TestCase as FlaskTestCase

from flask_profiler.configuration import Configuration
from flask_profiler.dependency_injector import DependencyInjector

from .basetest import BaseTest2, BasetTest


class EndpointMeasurementTest(BasetTest, FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        injector = DependencyInjector()
        self.controller = injector.get_filter_controller()

    def test_01_return_value(self):
        name = "john"
        response = self.client.get("/api/people/{}".format(name))
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, name)

    def test_02_without_profiler(self):
        config = Configuration(self.app)
        response = self.client.get("/api/without/profiler")
        r = response.data.decode("utf-8", "strict")

        self.assertEqual(r, "without profiler")
        measurements = list(
            config.collection.filter(self.controller.parse_filter(create_request()))
        )
        self.assertEqual(len(measurements), 0)

    def test_02_with_profiler(self) -> None:
        config = Configuration(self.app)
        response = self.client.get("/api/with/profiler/hello?q=1")
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, "with profiler")

        measurements = list(
            config.collection.filter(self.controller.parse_filter(create_request()))
        )
        self.assertEqual(len(measurements), 1)
        m = measurements[0]
        self.assertEqual(m.name, "/api/with/profiler/<message>")
        self.assertEqual(m.method, "GET")
        self.assertEqual(m.kwargs, {"message": "hello"})
        self.assertEqual(m.context.args, {"q": "1"})


class EndpointMeasurementTest2(BaseTest2, FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        injector = DependencyInjector()
        self.controller = injector.get_filter_controller()

    def test_01_profiler(self):
        config = Configuration(self.app)
        name = "foo"
        response = self.client.get("/api/people/{}".format(name))
        measurements = list(
            config.collection.filter(self.controller.parse_filter(create_request()))
        )
        self.assertEqual(len(measurements), 1)
        r = response.data.decode("utf-8", "strict")
        self.assertEqual(r, name)

    def test_02_profiler(self) -> None:
        config = Configuration(self.app)
        self.client.get("/api/people/foo")
        self.client.get("/api/people/foo")
        self.client.get("/api/with/profiler/hello?q=2")
        measurements = list(
            config.collection.filter(self.controller.parse_filter(create_request()))
        )
        self.assertEqual(len(measurements), 3)
        test_flag = False
        for list_element in measurements:
            if list_element.name == "/api/with/profiler/<message>":
                test_flag = True
                self.assertEqual(list_element.name, "/api/with/profiler/<message>")
                self.assertEqual(list_element.method, "GET")
                self.assertEqual(list_element.kwargs, {"message": "hello"})
                self.assertEqual(list_element.context.args, {"q": "2"})
        self.assertEqual(True, test_flag)

    def test_that_routes_with_uuids_get_profiled_correctly(self) -> None:
        config = Configuration(self.app)
        expected_uuid = uuid4()
        self.client.get(f"/api/people/by-id/{expected_uuid}")
        measurement = list(
            config.collection.filter(self.controller.parse_filter(create_request()))
        )[0]
        self.assertEqual(measurement.kwargs["id"], str(expected_uuid))


def create_request() -> Request:
    return Request(environ=dict())


if __name__ == "__main__":
    unittest.main()
