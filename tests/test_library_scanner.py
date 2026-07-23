"""Pruebas de la jerarquía física e inalterable de la biblioteca."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from database.manager import DatabaseManager
from library.scanner import scan_library


class LibraryScannerTests(unittest.TestCase):
    def test_direct_tracks_are_kept_as_loose_tracks_album(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "Biblioteca"
            track = root / "Ana Gabriel" / "01 canción.mp3"
            track.parent.mkdir(parents=True)
            track.touch()
            fake_details = SimpleNamespace(
                title="Canción", artist="Etiqueta incorrecta", track_number="1",
                year="", duration_seconds=120.0, file_format="MP3",
            )
            with patch("library.scanner.read_track_details", return_value=fake_details):
                scan = scan_library(root)
            self.assertEqual(scan.artists[0].name, "Ana Gabriel")
            self.assertEqual(scan.artists[0].albums[0].title, "Pistas sueltas")
            self.assertEqual(scan.artists[0].albums[0].tracks[0].track_artist, "Ana Gabriel")

    def test_playlist_like_folder_becomes_compilation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "Biblioteca"
            track = root / "Vallenatos Sueltos Spotify" / "01 canción.mp3"
            track.parent.mkdir(parents=True)
            track.touch()
            fake_details = SimpleNamespace(
                title="Canción", artist="Diomedes Díaz", track_number="1",
                year="", duration_seconds=120.0, file_format="MP3",
            )
            with patch("library.scanner.read_track_details", return_value=fake_details):
                scan = scan_library(root)
            album = scan.artists[0].albums[0]
            self.assertEqual(scan.artists[0].name, "Varios artistas")
            self.assertEqual(album.title, "Vallenatos Sueltos Spotify")
            self.assertTrue(album.is_compilation)
            self.assertEqual(album.tracks[0].track_artist, "Diomedes Díaz")

    def test_folder_names_override_conflicting_audio_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "Biblioteca"
            track = root / "Carlos Vives" / "Clásicos" / "01 - Prueba.mp3"
            track.parent.mkdir(parents=True)
            track.touch()
            fake_details = SimpleNamespace(
                title="La pista correcta",
                artist="Carlos Vives & Su Orquesta",
                album="Álbum incorrecto",
                track_number="1/10",
                year="2024",
                duration_seconds=185.5,
                file_format="MP3",
            )
            with patch("library.scanner.read_track_details", return_value=fake_details):
                scan = scan_library(root)

            self.assertEqual(scan.artists[0].name, "Carlos Vives")
            self.assertEqual(scan.artists[0].albums[0].title, "Clásicos")
            self.assertEqual(scan.artists[0].albums[0].tracks[0].title, "La pista correcta")

    def test_scan_can_be_saved_and_retrieved_as_a_playable_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "Música"
            track = root / "Carlos Vives" / "Clásicos" / "01 canción.mp3"
            track.parent.mkdir(parents=True)
            track.touch()
            fake_details = SimpleNamespace(
                title="Canción", track_number="01", year="",
                duration_seconds=120.0, file_format="MP3",
            )
            with patch("library.scanner.read_track_details", return_value=fake_details):
                scan = scan_library(root)
            database = DatabaseManager(base / "library.sqlite3")
            database.initialize()
            counts = database.import_library_scan(scan)

            self.assertEqual(counts, {"artists": 1, "albums": 1, "tracks": 1})
            artist = database.get_artists()[0]
            saved_track = database.get_tracks_for_artist(artist["id"])[0]
            self.assertEqual(saved_track["artist_name"], "Carlos Vives")
            self.assertEqual(saved_track["album_title"], "Clásicos")


    def test_sync_recognizes_moves_and_removes_deleted_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "Music"
            original = root / "Aventura" / "Album uno" / "01 tema.mp3"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"audio de prueba estable" * 100)
            fake_details = SimpleNamespace(
                title="Tema", artist="Etiqueta", track_number="1", year="",
                duration_seconds=180.0, file_format="MP3",
            )
            database = DatabaseManager(base / "library.sqlite3")
            database.initialize()
            with patch("library.scanner.read_track_details", return_value=fake_details):
                database.import_library_scan(scan_library(root))
            original_path = str(original.resolve())
            original_row = database.get_track_by_path(original_path)
            original_id = int(original_row["id"])
            for _ in range(3):
                database.record_qualified_listen(original_path, 60)
            playlist_id = database.create_playlist("Favoritas")
            database.add_track_to_playlist(playlist_id, original_path)

            with patch(
                "library.scanner.read_track_details",
                side_effect=ValueError("metadatos dañados"),
            ):
                damaged_scan = scan_library(root)
            damaged_result = database.synchronize_library_scan(damaged_scan)
            self.assertEqual(damaged_result["removed_tracks"], [])
            self.assertIsNotNone(database.get_track_by_path(original_path))

            moved = root / "Aventura" / "Album dos" / "Tema nuevo.mp3"
            moved.parent.mkdir(parents=True)
            original.rename(moved)
            moved_path = str(moved.resolve())
            with patch("library.scanner.read_track_details", return_value=fake_details):
                result = database.synchronize_library_scan(scan_library(root))

            self.assertEqual(result["moved_tracks"], {original_path: moved_path})
            moved_row = database.get_track_by_path(moved_path)
            self.assertEqual(int(moved_row["id"]), original_id)
            self.assertEqual(int(moved_row["play_count"]), 3)
            self.assertEqual(
                database.get_playlist_tracks(playlist_id)[0]["file_path"], moved_path
            )

            moved.unlink()
            with patch("library.scanner.read_track_details", return_value=fake_details):
                deleted = database.synchronize_library_scan(scan_library(root))
            self.assertEqual(deleted["removed_tracks"], [moved_path])
            self.assertIsNone(database.get_track_by_path(moved_path))
            self.assertEqual(database.get_playlist_tracks(playlist_id), [])
            self.assertEqual(database.get_albums(), [])
            self.assertEqual(database.get_artists(), [])

    def test_unchanged_files_reuse_cached_metadata_and_report_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "Music"
            track = root / "Aventura" / "Álbum" / "01 tema.mp3"
            track.parent.mkdir(parents=True)
            track.write_bytes(b"audio estable")
            stat = track.stat()
            cached = {
                str(track.resolve()): {
                    "title": "Tema guardado",
                    "track_artist": "Aventura",
                    "track_number": 1,
                    "duration": 180.0,
                    "file_format": "MP3",
                    "file_size": stat.st_size,
                    "modified_ns": stat.st_mtime_ns,
                    "file_signature": "firma",
                    "album_year": 2020,
                }
            }
            progress: list[tuple[int, int, str]] = []
            with patch("library.scanner.read_track_details") as reader:
                scan = scan_library(
                    root,
                    known_tracks=cached,
                    progress=lambda current, total, name: progress.append(
                        (current, total, name)
                    ),
                )
            reader.assert_not_called()
            self.assertEqual(
                scan.artists[0].albums[0].tracks[0].title, "Tema guardado"
            )
            self.assertEqual(progress[-1][:2], (1, 1))

    def test_manual_compilation_choice_survives_a_rescan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            root = base / "Music"
            track = root / "Aventura" / "Álbum" / "01 tema.mp3"
            track.parent.mkdir(parents=True)
            track.write_bytes(b"audio estable")
            details = SimpleNamespace(
                title="Tema", artist="Aventura", track_number="1", year="",
                duration_seconds=180.0, file_format="MP3",
            )
            database = DatabaseManager(base / "library.sqlite3")
            database.initialize()
            with patch("library.scanner.read_track_details", return_value=details):
                database.synchronize_library_scan(scan_library(root))
            album_id = int(database.get_albums(False)[0]["id"])
            database.set_album_compilation(album_id, True)
            with patch("library.scanner.read_track_details", return_value=details):
                database.synchronize_library_scan(scan_library(root))
            self.assertTrue(bool(database.get_album_by_id(album_id)["is_compilation"]))


if __name__ == "__main__":
    unittest.main()
