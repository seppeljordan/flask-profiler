import sqlite3
from unittest import TestCase

from flask_profiler.storage.sqlite.migrations import Migrations


class MigrationTests(TestCase):
    def test_can_run_migrations(self) -> None:
        connection = sqlite3.connect(":memory:")
        cursor = connection.cursor()
        migrations = Migrations()
        for migration in migrations.get_relevant_versions(0):
            migration.run(cursor)
        connection.commit()
