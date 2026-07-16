"""Pruebas basicas del esquema SQLite."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.manager import DatabaseManager


class DatabaseManagerTests(unittest.TestCase):
    def test_initialization_creates_expected_tables_and_empty_stats(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "test_library.sqlite3"
            database = DatabaseManager(database_path)
            database.initialize()

            tables = {
                row["name"]
                for row in database.fetch_all(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

            self.assertTrue({"albums", "tracks"}.issubset(tables))
            self.assertEqual(
                database.get_library_stats(),
                {"total_albums": 0, "albums": 0, "compilations": 0, "tracks": 0},
            )


if __name__ == "__main__":
    unittest.main()

