"""Búsqueda global de pistas de la biblioteca."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QMenu, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from database.manager import DatabaseManager
from ui.icons import navigation_icon
from ui.pages.collection_pages import _play_payload, _queue, mark_playing_track


class SearchPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._playing_file = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(8)
        title = QLabel("Buscar")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Encuentra una canción, artista o álbum en toda la biblioteca.")
        subtitle.setObjectName("pageSubtitle")
        self.search = QLineEdit()
        self.search.setObjectName("librarySearch")
        self.search.setPlaceholderText("Buscar canción, artista o álbum…")
        self.search.addAction(navigation_icon("search", "#8fa7c7"), QLineEdit.ActionPosition.LeadingPosition)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(450)
        self._search_timer.timeout.connect(self._run_search)
        self.search.textChanged.connect(self._schedule_search)
        self.search.returnPressed.connect(lambda: self.refresh(self.search.text()))
        self.results = QTreeWidget()
        self.results.setHeaderLabels(["TÍTULO", "ARTISTA", "ÁLBUM", "TIPO"])
        self.results.setRootIsDecorated(False)
        self.results.setAlternatingRowColors(True)
        self.results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self._context_menu)
        self.results.itemDoubleClicked.connect(self._play)
        self.results.setColumnWidth(0, 330)
        self.results.setColumnWidth(1, 210)
        self.results.setColumnWidth(2, 300)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.search)
        layout.addWidget(self.results, 1)

    def focus_search(self) -> None:
        self.search.setFocus()
        self.search.selectAll()

    def show_root(self) -> None:
        self._search_timer.stop()
        self.search.clear()
        self.results.clear()
        self.search.setFocus()

    def _schedule_search(self, _text: str) -> None:
        self._search_timer.start()

    def refresh(self, text: str) -> None:
        """Ejecuta inmediatamente; escribir normalmente usa la espera de 450 ms."""
        self._search_timer.stop()
        self._run_search(text)

    def _run_search(self, text: str | None = None) -> None:
        if text is None:
            text = self.search.text()
        self.results.clear()
        for row in self.database.search_tracks(text):
            artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
            item = QTreeWidgetItem([row["title"], artist, row["album_title"], row["file_format"]])
            context = {
                "artist_id": row["artist_id"], "album_id": row["album_id"],
                "is_compilation": bool(row["is_compilation"]), "file_path": row["file_path"],
            }
            item.setData(0, Qt.ItemDataRole.UserRole, context)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, _queue([row])[0])
            self.results.addTopLevelItem(item)
        if self._playing_file:
            mark_playing_track(self.results, self._playing_file, title_column=0)

    def _play(self, item: QTreeWidgetItem, _column: int) -> None:
        context = item.data(0, Qt.ItemDataRole.UserRole) or {}
        album_tracks = self.database.get_tracks_for_album(int(context["album_id"]))
        start = next(
            (
                index
                for index, track in enumerate(album_tracks)
                if track["file_path"] == context["file_path"]
            ),
            0,
        )
        self.play_requested.emit(_play_payload(album_tracks, start, context))

    def _context_menu(self, position: object) -> None:
        item = self.results.itemAt(position)
        if item is None:
            return
        self.results.setCurrentItem(item)
        menu = QMenu(self)
        add = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.results.viewport().mapToGlobal(position))
        if selected == add:
            self.enqueue_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))
        elif selected == playlist:
            self.playlist_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))

    def locate(self, file_path: str) -> bool:
        for index in range(self.results.topLevelItemCount()):
            item = self.results.topLevelItem(index)
            track = item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
            if track.get("file_path") == file_path:
                self.results.setCurrentItem(item)
                self.results.scrollToItem(item)
                return True
        return False

    def mark_playing(self, file_path: str) -> bool:
        return mark_playing_track(self.results, file_path, title_column=0)

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.results, file_path, title_column=0)
