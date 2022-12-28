from __future__ import annotations

from flask import Flask, g

from .entities import measurement_archive
from .sqlite import Sqlite


class DeferredArchivist:
    def __init__(self, configuration: Configuration) -> None:
        self.configuration = configuration

    def record_measurement(self, measurement: measurement_archive.Measurement) -> None:
        self.configuration.collection.record_measurement(measurement)

    def get_records(self) -> measurement_archive.RecordedMeasurements:
        return self.configuration.collection.get_records()


class Configuration:
    def __init__(self, app: Flask) -> None:
        self.app = app

    @property
    def enabled(self) -> bool:
        return self.read_config().get("enabled", False)

    @property
    def verbose(self) -> bool:
        return self.read_config().get("verbose", False)

    @property
    def url_prefix(self) -> str:
        return self.read_config().get("endpointRoot", "flask-profiler")

    @property
    def is_basic_auth_enabled(self) -> bool:
        return self.read_config().get("basicAuth", {}).get("enabled", False)

    @property
    def basic_auth_username(self) -> str:
        return self.read_config()["basicAuth"]["username"]

    @property
    def basic_auth_password(self) -> str:
        return self.read_config()["basicAuth"]["password"]

    @property
    def collection(self) -> measurement_archive.MeasurementArchivist:
        collection = g.get("flask_profiler_collection")
        if collection is None:
            collection = self._create_storage()
            g.flask_profiler_collection = collection
        return collection

    def _create_storage(self) -> measurement_archive.MeasurementArchivist:
        conf = self.read_config().get("storage", {})
        return Sqlite(
            sqlite_file=conf.get("FILE", "flask_profiler.sql"),
        )

    def read_config(self):
        return (
            self.app.config.get("flask_profiler")
            or self.app.config.get("FLASK_PROFILER")
            or dict()
        )
