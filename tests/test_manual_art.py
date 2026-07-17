"""Pruebas de persistencia para imágenes elegidas manualmente."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QColor, QImage

from library import cover_art, manual_art


class ManualArtworkTests(unittest.TestCase):
    def test_artist_and_album_images_are_saved_and_album_is_locked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "selected.png"
            image = QImage(40, 40, QImage.Format.Format_RGB32)
            image.fill(QColor("#176fe5"))
            self.assertTrue(image.save(str(source), "PNG"))

            with (
                patch.object(manual_art, "COVER_CACHE_DIR", root / "cache"),
                patch.object(cover_art, "COVER_CACHE_DIR", root / "cache"),
            ):
                artist_data = manual_art.save_manual_artist_image("Aventura", source)
                self.assertEqual(
                    manual_art.read_image(manual_art.manual_artist_image_path("Aventura")),
                    artist_data,
                )

                album_data = manual_art.save_manual_album_cover(
                    "God's Project", "Aventura", source
                )
                album_path = manual_art.manual_album_cover_path(
                    "God's Project", "Aventura"
                )
                self.assertEqual(manual_art.read_image(album_path), album_data)
                self.assertTrue(manual_art.is_manual_album_cover(album_path))


if __name__ == "__main__":
    unittest.main()
