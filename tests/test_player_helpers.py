"""Pruebas de utilidades del reproductor."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from player.controller import read_display_metadata
from ui.widgets.player_bar import format_milliseconds


class PlayerHelperTests(unittest.TestCase):
    def test_time_format_supports_minutes_and_hours(self) -> None:
        self.assertEqual(format_milliseconds(0), "0:00")
        self.assertEqual(format_milliseconds(65_000), "1:05")
        self.assertEqual(format_milliseconds(3_661_000), "1:01:01")

    def test_missing_metadata_uses_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "Mi canción.mp3"
            path.touch()
            with self.assertLogs("player.controller", level="WARNING"):
                title, artist = read_display_metadata(path)
            self.assertEqual(title, "Mi canción")
            self.assertEqual(artist, "Artista desconocido")


if __name__ == "__main__":
    unittest.main()
