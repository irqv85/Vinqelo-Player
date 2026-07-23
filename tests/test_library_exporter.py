from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from library.library_exporter import (
    LibraryExportWorker,
    build_library_relative_path,
    build_playlist_relative_path,
)


class CopyOnlyExportWorker(LibraryExportWorker):
    """Evita depender de FFmpeg al probar la lógica de sincronización."""

    def _convert(
        self, source: Path, output: Path, track: dict[str, object]
    ) -> None:
        output.write_bytes(source.read_bytes())


class LibraryExporterTests(unittest.TestCase):
    def test_builds_artist_album_track_hierarchy(self) -> None:
        track = {
            "file_path": r"C:\Music\Aventura\God's Project\01 Angelito.flac",
            "artist_name": "Aventura",
            "album_title": "God's Project",
            "is_compilation": 0,
        }
        self.assertEqual(
            build_library_relative_path(track),
            Path("Aventura") / "God's Project" / "01 Angelito.flac",
        )

    def test_compilations_have_their_own_hierarchy(self) -> None:
        track = {
            "file_path": r"C:\Music\Vallenatos varios\01 Tema.ogg",
            "artist_name": "Carpeta original",
            "album_title": "Vallenatos varios",
            "is_compilation": 1,
        }
        self.assertEqual(
            build_library_relative_path(track),
            Path("Compilaciones") / "Vallenatos varios" / "01 Tema.ogg",
        )

    def test_playlist_export_keeps_order_in_its_own_folder(self) -> None:
        track = {
            "file_path": r"C:\Music\Aventura\Tema original.flac",
            "title": "Mi canción favorita",
        }
        self.assertEqual(
            build_playlist_relative_path("Viaje", 7, track),
            Path("Listas de reproducción")
            / "Viaje"
            / "007 - Mi canción favorita.flac",
        )
        self.assertEqual(
            build_playlist_relative_path(
                "Global · Más escuchadas", 1, track, smart=True
            ).parts[0],
            "Listas inteligentes",
        )

    def test_sync_skips_unchanged_and_updates_changed_track(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "original.flac"
            source.write_bytes(b"primera version")
            destination = base / "usb"
            track = {
                "file_path": str(source),
                "relative_path": str(
                    Path("Aventura") / "God's Project" / source.name
                ),
                "file_signature": "signature-1",
                "file_size": source.stat().st_size,
                "duration": 60,
            }

            first_result: list[tuple[object, ...]] = []
            first = CopyOnlyExportWorker(
                [track], str(destination), "mp3", normalize=False, sync=True
            )
            first.finished.connect(lambda *result: first_result.append(result))
            first.run()
            self.assertEqual(first_result[0][1], 1)
            self.assertEqual(first_result[0][4], 0)

            second_result: list[tuple[object, ...]] = []
            second = CopyOnlyExportWorker(
                [track], str(destination), "mp3", normalize=False, sync=True
            )
            second.finished.connect(lambda *result: second_result.append(result))
            second.run()
            self.assertEqual(second_result[0][1], 0)
            self.assertEqual(second_result[0][4], 1)

            source.write_bytes(b"segunda version")
            track["file_signature"] = "signature-2"
            third_result: list[tuple[object, ...]] = []
            third = CopyOnlyExportWorker(
                [track], str(destination), "mp3", normalize=False, sync=True
            )
            third.finished.connect(lambda *result: third_result.append(result))
            third.run()
            self.assertEqual(third_result[0][1], 1)
            self.assertEqual(third_result[0][4], 0)


if __name__ == "__main__":
    unittest.main()
