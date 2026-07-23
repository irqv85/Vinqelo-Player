"""Regresiones del árbol de selección de la exportación."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from database.manager import DatabaseManager
from ui.library_export_dialog import LibraryExportDialog


class LibraryExportSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = DatabaseManager(
            Path(self.temporary.name) / "library.sqlite3"
        )
        self.database.initialize()
        connection = self.database.connect()
        try:
            root = connection.execute(
                "INSERT INTO library_roots(folder_path) VALUES (?)",
                ("C:/Music",),
            ).lastrowid
            artist_one = connection.execute(
                """INSERT INTO artists(root_id,name,folder_path)
                   VALUES (?,?,?)""",
                (root, "Artista Uno", "C:/Music/Artista Uno"),
            ).lastrowid
            artist_two = connection.execute(
                """INSERT INTO artists(root_id,name,folder_path)
                   VALUES (?,?,?)""",
                (root, "Artista Dos", "C:/Music/Artista Dos"),
            ).lastrowid
            self.album_ids: list[int] = []
            for artist_id, artist_name, album_name in (
                (artist_one, "Artista Uno", "Álbum A"),
                (artist_one, "Artista Uno", "Álbum B"),
                (artist_two, "Artista Dos", "Álbum C"),
            ):
                album_id = connection.execute(
                    """INSERT INTO albums(
                           artist_id,title,album_artist,folder_path
                       ) VALUES (?,?,?,?)""",
                    (
                        artist_id,
                        album_name,
                        artist_name,
                        f"C:/Music/{artist_name}/{album_name}",
                    ),
                ).lastrowid
                self.album_ids.append(int(album_id))
                connection.execute(
                    """INSERT INTO tracks(
                           album_id,title,track_artist,file_path,file_format
                       ) VALUES (?,?,?,?,?)""",
                    (
                        album_id,
                        f"Pista {album_name}",
                        artist_name,
                        f"C:/Music/{artist_name}/{album_name}/pista.mp3",
                        "MP3",
                    ),
                )
            connection.commit()
        finally:
            connection.close()
        self.parent = QWidget()
        self.dialog = LibraryExportDialog(self.database, self.parent)

    def tearDown(self) -> None:
        self.dialog.close()
        self.parent.close()
        self.temporary.cleanup()

    def _selected_albums(self) -> list[int]:
        return [
            int(source[1])
            for source in self.dialog.selected_sources()
            if source[0] == "album"
        ]

    def test_unchecking_root_clears_every_nested_album(self) -> None:
        root = self.dialog.tree.topLevelItem(0)
        self.assertEqual(set(self._selected_albums()), set(self.album_ids))

        root.setCheckState(0, Qt.CheckState.Unchecked)
        self.application.processEvents()

        self.assertEqual(self._selected_albums(), [])
        for artist_index in range(root.childCount()):
            artist = root.child(artist_index)
            self.assertEqual(
                artist.checkState(0), Qt.CheckState.Unchecked
            )
            for album_index in range(artist.childCount()):
                self.assertEqual(
                    artist.child(album_index).checkState(0),
                    Qt.CheckState.Unchecked,
                )

    def test_selecting_one_artist_exports_only_its_albums(self) -> None:
        root = self.dialog.tree.topLevelItem(0)
        root.setCheckState(0, Qt.CheckState.Unchecked)
        first_artist = root.child(0)
        first_artist.setCheckState(0, Qt.CheckState.Checked)
        self.application.processEvents()

        expected = {
            int(first_artist.child(index).data(
                0, Qt.ItemDataRole.UserRole
            )[1])
            for index in range(first_artist.childCount())
        }
        self.assertEqual(set(self._selected_albums()), expected)
        self.assertEqual(
            root.checkState(0), Qt.CheckState.PartiallyChecked
        )

    def test_selecting_one_album_exports_only_that_album(self) -> None:
        root = self.dialog.tree.topLevelItem(0)
        root.setCheckState(0, Qt.CheckState.Unchecked)
        album = root.child(0).child(0)
        album.setCheckState(0, Qt.CheckState.Checked)
        self.application.processEvents()

        selected_id = int(
            album.data(0, Qt.ItemDataRole.UserRole)[1]
        )
        self.assertEqual(self._selected_albums(), [selected_id])


if __name__ == "__main__":
    unittest.main()
