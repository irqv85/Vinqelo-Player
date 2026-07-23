"""Pruebas basicas del esquema SQLite."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database.manager import DatabaseManager


class DatabaseManagerTests(unittest.TestCase):
    def test_play_history_builds_top_artist_and_track_rankings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = DatabaseManager(Path(temporary_directory) / "library.sqlite3")
            database.initialize()
            connection = database.connect()
            try:
                root_id = connection.execute(
                    "INSERT INTO library_roots(folder_path) VALUES ('C:/Music')"
                ).lastrowid
                artist_id = connection.execute(
                    "INSERT INTO artists(root_id,name,folder_path) VALUES (?,?,?)",
                    (root_id, "Luis Miguel", "C:/Music/Luis Miguel"),
                ).lastrowid
                album_id = connection.execute(
                    """INSERT INTO albums(artist_id,title,album_artist,folder_path)
                       VALUES (?,?,?,?)""",
                    (artist_id, "Mis Romances", "Luis Miguel", "C:/Music/Luis Miguel/Mis Romances"),
                ).lastrowid
                connection.execute(
                    """INSERT INTO tracks(album_id,title,track_artist,file_path,file_format)
                       VALUES (?,?,?,?,?)""",
                    (album_id, "No me platiques más", "Luis Miguel", "C:/Music/song.mp3", "MP3"),
                )
                connection.commit()
            finally:
                connection.close()

            database.record_track_play("C:/Music/song.mp3")
            database.record_track_play("C:/Music/song.mp3")
            self.assertEqual(database.get_top_artists(), [])
            self.assertEqual(database.get_top_tracks(), [])
            database.record_track_play("C:/Music/song.mp3")
            self.assertEqual(database.get_top_artists()[0]["play_count"], 3)
            self.assertEqual(database.get_top_tracks()[0]["play_count"], 3)

            connection = database.connect()
            try:
                connection.execute(
                    """INSERT INTO tracks(album_id,title,track_artist,file_path,file_format)
                       VALUES (?,?,?,?,?)""",
                    (album_id, "Ahora te puedes marchar", "Luis Miguel", "C:/Music/song2.mp3", "MP3"),
                )
                connection.commit()
            finally:
                connection.close()
            for _ in range(3):
                database.record_qualified_listen("C:/Music/song2.mp3", 100)
            database.add_listen_time("C:/Music/song.mp3", 90)
            self.assertEqual(database.get_top_tracks()[0]["file_path"], "C:/Music/song2.mp3")
            self.assertEqual(database.get_top_tracks()[0]["listen_seconds"], 300)
            self.assertEqual(database.get_top_artists()[0]["listen_seconds"], 390)
            self.assertEqual(
                database.get_smart_tracks_global()[0]["file_path"],
                "C:/Music/song2.mp3",
            )
            self.assertEqual(
                database.get_smart_tracks_for_artist(artist_id)[0]["file_path"],
                "C:/Music/song2.mp3",
            )
            self.assertEqual(
                database.get_smart_tracks_new()[0]["file_path"],
                "C:/Music/song2.mp3",
            )
            self.assertEqual(database.get_smart_playlist_artists()[0]["id"], artist_id)

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

            self.assertTrue(
                {
                    "library_roots", "artists", "albums", "tracks",
                    "playlists", "playlist_tracks",
                }.issubset(tables)
            )
            self.assertEqual(
                database.get_library_stats(),
                {
                    "total_albums": 0,
                    "albums": 0,
                    "compilations": 0,
                    "tracks": 0,
                    "artists": 0,
                    "roots": 0,
                },
            )
            self.assertEqual(
                database.get_media_summary(),
                {"total_duration": 0, "formats": []},
            )

    def test_media_summary_groups_formats_and_estimates_average_bitrate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = DatabaseManager(
                Path(temporary_directory) / "library.sqlite3"
            )
            database.initialize()
            connection = database.connect()
            try:
                root = connection.execute(
                    "INSERT INTO library_roots(folder_path) VALUES (?)",
                    ("C:/Music",),
                ).lastrowid
                artist = connection.execute(
                    "INSERT INTO artists(root_id,name,folder_path) VALUES (?,?,?)",
                    (root, "Artista", "C:/Music/Artista"),
                ).lastrowid
                album = connection.execute(
                    """INSERT INTO albums
                       (artist_id,title,album_artist,folder_path)
                       VALUES (?,?,?,?)""",
                    (artist, "Álbum", "Artista", "C:/Music/Artista/Album"),
                ).lastrowid
                connection.execute(
                    """INSERT INTO tracks
                       (album_id,title,track_artist,file_path,duration,
                        file_format,file_size)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        album, "Tema", "Artista", "C:/Music/tema.mp3",
                        100.0, "mp3", 2_000_000,
                    ),
                )
                connection.commit()
            finally:
                connection.close()
            summary = database.get_media_summary()
            self.assertEqual(summary["total_duration"], 100.0)
            self.assertEqual(summary["formats"][0]["file_format"], "MP3")
            self.assertEqual(summary["formats"][0]["track_count"], 1)
            self.assertEqual(round(summary["formats"][0]["average_bitrate"]), 160)

    def test_search_finds_title_artist_and_album(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = DatabaseManager(Path(temporary_directory) / "library.sqlite3")
            database.initialize()
            connection = database.connect()
            try:
                root_id = connection.execute(
                    "INSERT INTO library_roots(folder_path) VALUES ('C:/Music')"
                ).lastrowid
                artist_id = connection.execute(
                    "INSERT INTO artists(root_id,name,folder_path) VALUES (?,?,?)",
                    (root_id, "Aventura", "C:/Music/Aventura"),
                ).lastrowid
                album_id = connection.execute(
                    "INSERT INTO albums(artist_id,title,album_artist,folder_path) VALUES (?,?,?,?)",
                    (artist_id, "God's Project", "Aventura", "C:/Music/Aventura/Gods Project"),
                ).lastrowid
                connection.execute(
                    "INSERT INTO tracks(album_id,title,track_artist,file_path,file_format) VALUES (?,?,?,?,?)",
                    (album_id, "Ella y yo", "Aventura", "C:/Music/ella.mp3", "MP3"),
                )
                connection.commit()
            finally:
                connection.close()

            self.assertEqual(database.search_tracks("Ella Aventura")[0]["title"], "Ella y yo")
            self.assertEqual(database.search_tracks("God's Project")[0]["artist_name"], "Aventura")

    def test_user_playlist_keeps_order_and_avoids_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = DatabaseManager(Path(temporary_directory) / "library.sqlite3")
            database.initialize()
            connection = database.connect()
            try:
                root = connection.execute(
                    "INSERT INTO library_roots(folder_path) VALUES (?)", ("C:/Music",)
                ).lastrowid
                artist = connection.execute(
                    "INSERT INTO artists(root_id,name,folder_path) VALUES (?,?,?)",
                    (root, "Aventura", "C:/Music/Aventura"),
                ).lastrowid
                album = connection.execute(
                    "INSERT INTO albums(artist_id,title,album_artist,folder_path) VALUES (?,?,?,?)",
                    (artist, "Obsesión", "Aventura", "C:/Music/Aventura/Obsesion"),
                ).lastrowid
                for title, path in (("Uno", "C:/Music/1.mp3"), ("Dos", "C:/Music/2.mp3")):
                    connection.execute(
                        "INSERT INTO tracks(album_id,title,track_artist,file_path,file_format) VALUES (?,?,?,?,?)",
                        (album, title, "Aventura", path, "MP3"),
                    )
                connection.commit()
            finally:
                connection.close()

            playlist = database.create_playlist("Favoritas")
            self.assertTrue(database.add_track_to_playlist(playlist, "C:/Music/2.mp3"))
            self.assertTrue(database.add_track_to_playlist(playlist, "C:/Music/1.mp3"))
            self.assertFalse(database.add_track_to_playlist(playlist, "C:/Music/2.mp3"))
            self.assertEqual(
                [row["title"] for row in database.get_playlist_tracks(playlist)],
                ["Dos", "Uno"],
            )

    def test_title_edit_renames_file_and_updates_library_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            source = folder / "track 01.mp3"
            source.write_bytes(b"not real audio")
            database = DatabaseManager(folder / "library.sqlite3")
            database.initialize()
            connection = database.connect()
            try:
                root = connection.execute(
                    "INSERT INTO library_roots(folder_path) VALUES (?)", (str(folder),)
                ).lastrowid
                artist = connection.execute(
                    "INSERT INTO artists(root_id,name,folder_path) VALUES (?,?,?)",
                    (root, "Artista", str(folder / "Artista")),
                ).lastrowid
                album = connection.execute(
                    "INSERT INTO albums(artist_id,title,album_artist,folder_path) VALUES (?,?,?,?)",
                    (artist, "Álbum", "Artista", str(folder / "Artista" / "Álbum")),
                ).lastrowid
                connection.execute(
                    "INSERT INTO tracks(album_id,title,track_artist,file_path,file_format) VALUES (?,?,?,?,?)",
                    (album, "track 01", "Artista", str(source), "MP3"),
                )
                connection.commit()
            finally:
                connection.close()

            with patch("mutagen.File", return_value=None):
                new_path = Path(database.update_track_title(str(source), "Mi: canción"))
            self.assertEqual(new_path.name, "Mi_ canción.mp3")
            self.assertTrue(new_path.exists())
            self.assertFalse(source.exists())
            row = database.get_track_by_path(str(new_path))
            self.assertEqual(row["title"], "Mi: canción")


if __name__ == "__main__":
    unittest.main()
