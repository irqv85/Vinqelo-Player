"""Listas de reproducción creadas por el usuario."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from ui.pages.collection_pages import (
    _play_payload, _queue, _total_duration, connect_track_click,
    mark_playing_track,
)
from ui.playlist_export import PlaylistExportController


class PlaylistsPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._playlist_id: int | None = None
        self._playing_file = ""
        self._exporter = PlaylistExportController(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(8)
        title = QLabel("Listas de reproducción")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Crea tus propias listas y conserva el orden de reproducción.")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(12)
        left = QVBoxLayout()
        self.create_button = QPushButton("+  Nueva lista")
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self.create_playlist)
        self.playlists = QListWidget()
        self.playlists.setObjectName("smartPlaylistList")
        self.playlists.currentItemChanged.connect(self._select_playlist)
        self.playlists.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlists.customContextMenuRequested.connect(self._playlist_menu)
        left.addWidget(self.create_button)
        left.addWidget(self.playlists, 1)

        right = QVBoxLayout()
        heading = QHBoxLayout()
        self.list_title = QLabel("Selecciona o crea una lista")
        self.list_title.setObjectName("sectionTitle")
        self.export_button = QPushButton("Exportar")
        self.export_button.setObjectName("primaryButton")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._export_playlist)
        heading.addWidget(self.list_title, 1)
        heading.addWidget(self.export_button)
        self.tracks = QTreeWidget()
        self.tracks.setHeaderLabels(["#", "TÍTULO", "ARTISTA", "ÁLBUM", "DURACIÓN"])
        self.tracks.setRootIsDecorated(False)
        self.tracks.setAlternatingRowColors(True)
        self.tracks.setColumnWidth(0, 45)
        self.tracks.setColumnWidth(1, 310)
        self.tracks.setColumnWidth(2, 190)
        self.tracks.setColumnWidth(3, 240)
        connect_track_click(self.tracks, self._play)
        self.tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks.customContextMenuRequested.connect(self._track_menu)
        right.addLayout(heading)
        right.addWidget(self.tracks, 1)

        body.addLayout(left, 0)
        body.addLayout(right, 1)
        body.setStretch(0, 1)
        body.setStretch(1, 3)
        root.addSpacing(8)
        root.addLayout(body, 1)
        self.refresh()

    def create_playlist(self) -> int | None:
        name, accepted = QInputDialog.getText(self, "Nueva lista", "Nombre de la lista:")
        if not accepted or not name.strip():
            return None
        try:
            playlist_id = self.database.create_playlist(name)
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo crear", str(exc))
            return None
        self.refresh(select_id=playlist_id)
        return playlist_id

    def refresh(self, *, select_id: int | None = None) -> None:
        selected = select_id if select_id is not None else self._playlist_id
        self.playlists.blockSignals(True)
        self.playlists.clear()
        item_to_select = None
        for row in self.database.get_playlists():
            count = int(row["track_count"])
            item = QListWidgetItem(str(row["name"]))
            item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
            item.setData(Qt.ItemDataRole.UserRole + 1, row["name"])
            item.setData(Qt.ItemDataRole.UserRole + 2, count)
            item.setData(Qt.ItemDataRole.UserRole + 3, float(row["total_duration"]))
            item.setToolTip(
                f'{count} pistas · {_total_duration(row["total_duration"])}'
            )
            self.playlists.addItem(item)
            if int(row["id"]) == selected:
                item_to_select = item
        self.playlists.blockSignals(False)
        if item_to_select is not None:
            self.playlists.setCurrentItem(item_to_select)
            self._load_tracks()
        elif self.playlists.count():
            self.playlists.setCurrentRow(0)
        else:
            self._playlist_id = None
            self.export_button.setEnabled(False)
            self.tracks.clear()
            self.list_title.setText("Selecciona o crea una lista")

    def _select_playlist(self, current: QListWidgetItem | None, _previous: object) -> None:
        self._playlist_id = (
            int(current.data(Qt.ItemDataRole.UserRole)) if current is not None else None
        )
        self.export_button.setEnabled(self._playlist_id is not None)
        self._load_tracks()

    def _export_playlist(self) -> None:
        if self._playlist_id is None:
            return
        item = self.playlists.currentItem()
        name = str(item.data(Qt.ItemDataRole.UserRole + 1)) if item else "Playlist"
        self._exporter.start(name, self.database.get_playlist_tracks(self._playlist_id))

    def _load_tracks(self) -> None:
        self.tracks.clear()
        if self._playlist_id is None:
            return
        selected = self.playlists.currentItem()
        if selected is not None:
            name = str(selected.data(Qt.ItemDataRole.UserRole + 1))
            count = int(selected.data(Qt.ItemDataRole.UserRole + 2) or 0)
            duration = float(selected.data(Qt.ItemDataRole.UserRole + 3) or 0)
            self.list_title.setText(
                f"{name} · {count} pistas · {_total_duration(duration)}"
            )
        for row in self.database.get_playlist_tracks(self._playlist_id):
            artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
            duration = int(float(row["duration"] or 0))
            item = QTreeWidgetItem(
                [
                    str(row["position"]),
                    row["title"],
                    artist or "Artista desconocido",
                    row["album_title"],
                    f"{duration // 60}:{duration % 60:02d}",
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, _queue([row])[0])
            self.tracks.addTopLevelItem(item)
        mark_playing_track(self.tracks, self._playing_file, title_column=1)

    def _play(self, item: QTreeWidgetItem, _column: int) -> None:
        if self._playlist_id is None:
            return
        rows = self.database.get_playlist_tracks(self._playlist_id)
        start = self.tracks.indexOfTopLevelItem(item)
        self.play_requested.emit(_play_payload(rows, start, {"playlist_id": self._playlist_id}))

    def _track_menu(self, position: object) -> None:
        item = self.tracks.itemAt(position)
        if item is None or self._playlist_id is None:
            return
        self.tracks.setCurrentItem(item)
        menu = QMenu(self)
        enqueue = menu.addAction("Añadir a la cola")
        remove = menu.addAction("Quitar de esta lista")
        selected = menu.exec(self.tracks.viewport().mapToGlobal(position))
        track = item.data(0, Qt.ItemDataRole.UserRole) or {}
        if selected == enqueue:
            self.enqueue_requested.emit(track)
        elif selected == remove:
            self.database.remove_track_from_playlist(
                self._playlist_id, str(track.get("file_path", ""))
            )
            self.refresh(select_id=self._playlist_id)

    def _playlist_menu(self, position: object) -> None:
        item = self.playlists.itemAt(position)
        if item is None:
            return
        self.playlists.setCurrentItem(item)
        menu = QMenu(self)
        export = menu.addAction("Exportar como compilacion...")
        menu.addSeparator()
        delete = menu.addAction("Eliminar lista")
        selected = menu.exec(self.playlists.viewport().mapToGlobal(position))
        if selected == export:
            self._export_playlist()
        elif selected == delete:
            name = str(item.data(Qt.ItemDataRole.UserRole + 1))
            answer = QMessageBox.question(
                self, "Eliminar lista", f'¿Eliminar la lista “{name}”?'
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.database.delete_playlist(int(item.data(Qt.ItemDataRole.UserRole)))
                self._playlist_id = None
                self.refresh()

    def show_root(self) -> None:
        self.refresh()

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.tracks, file_path, title_column=1)
