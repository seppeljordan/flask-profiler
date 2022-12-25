import sqlite3
from unittest import TestCase

from flask_profiler.storage.sqlite.migrations import Migrations


class MigrationTests(TestCase):
    def test_can_run_migrations(self) -> None:
        connection = sqlite3.connect(":memory:")
        migrations = Migrations(connection)
        migrations.run_necessary_migrations()
