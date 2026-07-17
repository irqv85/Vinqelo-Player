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


if __name__ == "__main__":
    unittest.main()
