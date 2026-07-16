"""Conexion y operaciones basicas de la biblioteca SQLite."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any


class DatabaseManager:
    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self._logger = logging.getLogger(__name__)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path = Path(__file__).with_name("schema.sql")
        schema = schema_path.read_text(encoding="utf-8")

        connection = self.connect()
        try:
            connection.executescript(schema)
            connection.execute("PRAGMA journal_mode = WAL")
            connection.commit()
        finally:
            connection.close()

        self._logger.info("Base de datos preparada en %s", self.database_path)

    def get_library_stats(self) -> dict[str, int]:
        query = """
            SELECT
                COUNT(*) AS total_albums,
                COALESCE(SUM(CASE WHEN is_compilation = 0 THEN 1 ELSE 0 END), 0)
                    AS albums,
                COALESCE(SUM(CASE WHEN is_compilation = 1 THEN 1 ELSE 0 END), 0)
                    AS compilations
            FROM albums
        """
        connection = self.connect()
        try:
            album_row = connection.execute(query).fetchone()
            track_row = connection.execute("SELECT COUNT(*) AS tracks FROM tracks").fetchone()
        finally:
            connection.close()

        return {
            "total_albums": int(album_row["total_albums"]),
            "albums": int(album_row["albums"]),
            "compilations": int(album_row["compilations"]),
            "tracks": int(track_row["tracks"]),
        }

    def fetch_all(self, query: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        connection = self.connect()
        try:
            return list(connection.execute(query, parameters).fetchall())
        finally:
            connection.close()
