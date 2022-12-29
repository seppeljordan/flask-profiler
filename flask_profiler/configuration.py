from __future__ import annotations

from logging import getLogger
from typing import Protocol

from flask import Flask, g

from .database import Database
from .entities import measurement_archive
from .fallback_storage import MeasurementArchivistPlaceholder
from .sqlite import Sqlite

logger = getLogger(__name__)


class MeasurementDatabase(measurement_archive.MeasurementArchivist, Database, Protocol):
    ...


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
        if "flask_profiler_collection" not in g:
            g.flask_profiler_collection = self._create_storage()

        return g.flask_profiler_collection

    @classmethod
    def cleanup_appcontext(cls, exception) -> None:
        logger.debug("Starting cleanup")
        db = g.pop("flask_profiler_collection", None)
        if db:
            logger.debug("Destroy database connection")
            db.close_connection()

    def _create_storage(self) -> MeasurementDatabase:
        logger.debug("Creating measurement database")
        storage: MeasurementDatabase
        conf = self.read_config().get("storage", {})
        try:
            storage = Sqlite(
                sqlite_file=conf.get("FILE", "flask_profiler.sql"),
            )
        except Exception as e:
            logger.error("Failed to initialize measurement storage")
            logger.exception(e)
            storage = MeasurementArchivistPlaceholder()
        return storage

    def read_config(self):
        return (
            self.app.config.get("flask_profiler")
            or self.app.config.get("FLASK_PROFILER")
            or dict()
        )
