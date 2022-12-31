import pathlib
import shutil
import tempfile

from flask import Flask
from flask_testing import TestCase

from flask_profiler import init_app


class BasicAuthTests(TestCase):
    app: Flask

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.data_dir)

    def create_app(self) -> Flask:
        self.data_dir = pathlib.Path(tempfile.mkdtemp())
        self.expected_username = "testusername"
        self.expected_password = "test password"
        app = Flask("Authentication test app")
        app.config["flask_profiler"] = dict(
            enabled=True,
            endpointRoot="profiling",
            storage=dict(
                FILE=str(self.data_dir / "db.sql"),
            ),
            basicAuth=dict(
                enabled=True,
                username=self.expected_username,
                password=self.expected_password,
            ),
        )

        init_app(app)
        return app

    def test_that_index_page_can_be_accessed_when_authenticated(self) -> None:
        response = self.client.get(
            "/profiling/", auth=(self.expected_username, self.expected_password)
        )
        assert response.status_code == 200

    def test_that_index_page_cannot_be_accessed_not_authenticated(self) -> None:
        response = self.client.get("/profiling/")
        assert response.status_code == 401
