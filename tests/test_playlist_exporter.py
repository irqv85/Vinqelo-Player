from __future__ import annotations

import tempfile
import unittest
import shutil
from pathlib import Path

from library.playlist_exporter import (
    EXPORT_AUDIO_PROFILES, PlaylistExportWorker, safe_filename,
)


class PlaylistExporterTests(unittest.TestCase):
    def test_exports_flat_ordered_compilation_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source_a = base / "original-a.mp3"
            source_b = base / "original-b.mp3"
            source_a.write_bytes(b"a")
            source_b.write_bytes(b"b")
            destination = base / "pendrive"
            destination.mkdir()
            results: list[tuple[object, ...]] = []
            worker = PlaylistExportWorker(
                "Mi Playlist",
                [
                    {"title": "Segunda / canción", "file_path": str(source_b)},
                    {"title": "Primera", "file_path": str(source_a)},
                ],
                str(destination),
                "mp3",
            )
            worker.finished.connect(lambda *values: results.append(values))
            worker._convert = lambda source, output: shutil.copy2(source, output)
            worker.run()

            folder = destination / "Mi Playlist"
            self.assertEqual(
                [path.name for path in folder.iterdir()],
                ["01 - Segunda _ canción.mp3", "02 - Primera.mp3"],
            )
            self.assertFalse(any(path.is_dir() for path in folder.iterdir()))
            self.assertEqual(results[0][1], 2)
            self.assertEqual(results[0][2], [])
            self.assertFalse(results[0][3])

    def test_safe_filename_removes_windows_invalid_characters(self) -> None:
        self.assertEqual(safe_filename('Lista: 2026?'), "Lista_ 2026_")

    def test_all_export_profiles_target_128_kbps(self) -> None:
        for profile in EXPORT_AUDIO_PROFILES.values():
            self.assertIn("-b:a", profile)
            self.assertEqual(profile[profile.index("-b:a") + 1], "128k")


if __name__ == "__main__":
    unittest.main()
