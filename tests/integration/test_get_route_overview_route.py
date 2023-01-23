import pathlib
import shutil
import tempfile

from flask import Flask
from flask_testing import TestCase

from flask_profiler import init_app


class BasicAuthTests(TestCase):
    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.data_dir)

    def create_app(self) -> Flask:
        self.data_dir = pathlib.Path(tempfile.mkdtemp())
        app = Flask("Authentication test app")
        app.config["flask_profiler"] = dict(
            enabled=True,
            endpointRoot="profiling",
            storage=dict(
                FILE=str(self.data_dir / "db.sql"),
            ),
            basicAuth=dict(
                enabled=False,
            ),
        )

        @app.route("/")
        def hello_world() -> str:
            return "<p>Hello, World!</p>"

        init_app(app)
        return app

    def test_can_access_a_routes_overview_page(self) -> None:
        assert self.client.get("/").status_code == 200
        assert self.client.get("/profiling/route/hello_world").status_code == 200

    def test_cannot_access_a_routes_overview_page_for_a_non_existing_route(
        self,
    ) -> None:
        assert self.client.get("/profiling/route/i-dont-exist").status_code == 404
