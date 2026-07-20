"""Listas inteligentes generadas a partir del tiempo real de escucha."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QPushButton,
)

from database.manager import DatabaseManager
from ui.pages.collection_pages import (
    _play_payload, _queue, _total_duration, mark_playing_track,
)
from ui.pages.library_page import format_listening_time
from ui.playlist_export import PlaylistExportController
from ui.i18n import translate_text


class SmartPlaylistsPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._playing_file = ""
        self._rows: list[object] = []
        self._exporter = PlaylistExportController(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        title = QLabel("Listas inteligentes")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Listas automáticas ordenadas por tiempo acumulado de reproducción.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        content = QHBoxLayout()
        content.setSpacing(12)
        self.playlists = QListWidget()
        self.playlists.setObjectName("smartPlaylistList")
        self.playlists.setFixedWidth(265)
        self.playlists.currentItemChanged.connect(self._playlist_changed)
        content.addWidget(self.playlists)

        right = QVBoxLayout()
        heading_row = QHBoxLayout()
        self.heading = QLabel("")
        self.heading.setObjectName("pageTitle")
        self.export_button = QPushButton("Exportar")
        self.export_button.setObjectName("primaryButton")
        self.export_button.clicked.connect(self._export_playlist)
        heading_row.addWidget(self.heading, 1)
        heading_row.addWidget(self.export_button)
        self.tracks = QTreeWidget()
        self.tracks.setHeaderLabels(["TÍTULO", "ARTISTA", "ÁLBUM", "TIEMPO"])
        self.tracks.setRootIsDecorated(False)
        self.tracks.setAlternatingRowColors(True)
        self.tracks.setColumnWidth(0, 330)
        self.tracks.setColumnWidth(1, 190)
        self.tracks.setColumnWidth(2, 260)
        self.tracks.itemDoubleClicked.connect(self._play_track)
        self.tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks.customContextMenuRequested.connect(self._context_menu)
        right.addLayout(heading_row)
        right.addWidget(self.tracks, 1)
        content.addLayout(right, 1)
        layout.addLayout(content, 1)

    def refresh(self) -> None:
        self.playlists.clear()
        self._add_playlist(translate_text("Global · Más escuchadas"), "global", None)
        self._add_playlist(translate_text("New · Últimos 30 días"), "new", None)
        header = QListWidgetItem(translate_text("POR ARTISTA"))
        header.setFlags(Qt.ItemFlag.NoItemFlags)
        header.setSizeHint(QSize(0, 34))
        self.playlists.addItem(header)
        for artist in self.database.get_smart_playlist_artists():
            item = self._add_playlist(artist["name"], "artist", int(artist["id"]))
            item.setToolTip(
                translate_text(f'{format_listening_time(artist["listen_seconds"])} escuchados')
            )
        self.playlists.setCurrentRow(0)

    def _add_playlist(self, label: str, kind: str, value: int | None) -> QListWidgetItem:
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, (kind, value))
        item.setSizeHint(QSize(0, 42))
        self.playlists.addItem(item)
        return item

    def _playlist_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None or not current.flags():
            return
        kind, value = current.data(Qt.ItemDataRole.UserRole)
        if kind == "global":
            self._rows = self.database.get_smart_tracks_global()
        elif kind == "new":
            self._rows = self.database.get_smart_tracks_new()
        else:
            self._rows = self.database.get_smart_tracks_for_artist(int(value))
        total_duration = sum(float(row["duration"] or 0) for row in self._rows)
        count = translate_text(f"{len(self._rows)} pistas")
        self.heading.setText(f"{current.text()} · {count} · {_total_duration(total_duration)}")
        self._fill_tracks()

    def _export_playlist(self) -> None:
        current = self.playlists.currentItem()
        if current is None or not current.data(Qt.ItemDataRole.UserRole):
            return
        self._exporter.start(current.text(), self._rows)

    def _fill_tracks(self) -> None:
        self.tracks.clear()
        if not self._rows:
            empty = QTreeWidgetItem([translate_text("Aún no hay escuchas suficientes para esta lista."), "", "", ""])
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self.tracks.addTopLevelItem(empty)
            return
        for index, row in enumerate(self._rows):
            artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
            item = QTreeWidgetItem(
                [row["title"], artist, row["album_title"], format_listening_time(row["listen_seconds"])]
            )
            context = {
                "artist_id": row["artist_id"], "album_id": row["album_id"],
                "is_compilation": bool(row["is_compilation"]), "file_path": row["file_path"],
            }
            item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(self._rows, index, context))
            item.setData(0, Qt.ItemDataRole.UserRole + 1, _queue([row])[0])
            self.tracks.addTopLevelItem(item)
        if self._playing_file:
            mark_playing_track(self.tracks, self._playing_file, title_column=0)

    def _play_track(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if payload:
            self.play_requested.emit(payload)

    def _context_menu(self, position: object) -> None:
        item = self.tracks.itemAt(position)
        if item is None or not item.data(0, Qt.ItemDataRole.UserRole + 1):
            return
        self.tracks.setCurrentItem(item)
        menu = QMenu(self)
        add = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.tracks.viewport().mapToGlobal(position))
        if selected == add:
            self.enqueue_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))
        elif selected == playlist:
            self.playlist_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))

    def show_root(self) -> None:
        self.refresh()

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.tracks, file_path, title_column=0)
