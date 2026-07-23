"""Navegador de carpetas con vista de iconos y lista de pistas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListView,
    QListWidget, QListWidgetItem, QMenu, QMessageBox, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from database.manager import DatabaseManager
from ui.album_metadata_dialog import AlbumMetadataDialog
from ui.icons import library_folder_icon, navigation_icon
from ui.i18n import translate_text
from ui.pages.collection_pages import (
    _play_payload,
    _queue,
    connect_track_click,
    mark_playing_track,
)


class FoldersPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)
    metadata_changed = Signal(object)
    classification_changed = Signal()

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._playing_file = ""
        self._level: tuple[str, int | None] = ("home", None)
        self._history: list[tuple[str, int | None]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(8)
        title = QLabel("Carpetas")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Navega como en el Explorador y abre las carpetas con doble clic.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.back_button = QPushButton("Atrás")
        self.back_button.clicked.connect(self._go_back)
        self.path_label = QLabel("Biblioteca")
        self.path_label.setObjectName("sectionTitle")
        self.search = QLineEdit()
        self.search.setObjectName("folderSearch")
        self.search.setPlaceholderText("Buscar en esta carpeta")
        self.search.setClearButtonEnabled(True)
        self.search.addAction(
            navigation_icon("search", "#8fa7c7"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.setMaximumWidth(285)
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(420)
        self._filter_timer.timeout.connect(self._apply_filter)
        self.search.textChanged.connect(lambda: self._filter_timer.start())
        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.path_label, 1)
        toolbar.addWidget(self.search)
        layout.addLayout(toolbar)

        self.folders = QListWidget()
        self.folders.setObjectName("folderExplorer")
        self.folders.setViewMode(QListView.ViewMode.IconMode)
        self.folders.setIconSize(QSize(54, 54))
        self.folders.setGridSize(QSize(170, 104))
        self.folders.setResizeMode(QListView.ResizeMode.Adjust)
        self.folders.setMovement(QListView.Movement.Static)
        self.folders.setWordWrap(True)
        self.folders.itemDoubleClicked.connect(self._open_folder)
        self.folders.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folders.customContextMenuRequested.connect(self._folder_menu)
        layout.addWidget(self.folders, 1)

        self.track_heading = QLabel("Pistas")
        self.track_heading.setObjectName("sectionTitle")
        self.tracks = QTreeWidget()
        self.tracks.setHeaderLabels(["#", "TÍTULO", "ARTISTA", "DURACIÓN", "TIPO"])
        self.tracks.setRootIsDecorated(False)
        self.tracks.setAlternatingRowColors(True)
        self.tracks.setUniformRowHeights(True)
        self.tracks.setColumnWidth(0, 45)
        self.tracks.setColumnWidth(1, 350)
        self.tracks.setColumnWidth(2, 220)
        connect_track_click(self.tracks, self._play_track)
        self.tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks.customContextMenuRequested.connect(self._track_menu)
        layout.addWidget(self.track_heading)
        layout.addWidget(self.tracks, 2)
        self.refresh()

    def refresh(self) -> None:
        self._display(*self._level, remember=False)

    def show_root(self) -> None:
        self._history.clear()
        self.search.clear()
        self._display("home", None, remember=False)

    def _display(self, kind: str, value: int | None, *, remember: bool = True) -> None:
        if remember and self._level != (kind, value):
            self._history.append(self._level)
        self._level = (kind, value)
        self.back_button.setEnabled(bool(self._history))
        self.folders.clear()
        self.tracks.clear()
        path_text = "Biblioteca"
        nodes: list[tuple[object, str]] = []
        track_rows: list[object] = []
        if kind == "home":
            nodes = [(row, "root") for row in self.database.get_roots()]
        elif kind == "root" and value is not None:
            root = next((row for row in self.database.get_roots() if int(row["id"]) == value), None)
            path_text = str(root["folder_path"]) if root else path_text
            nodes = [(row, "artist") for row in self.database.get_artists_for_root(value)]
        elif kind == "artist" and value is not None:
            artist = self.database.get_artist_by_id(value)
            path_text = str(artist["folder_path"]) if artist else path_text
            nodes = [(row, "album") for row in self.database.get_albums_for_artist(value)]
        elif kind == "album" and value is not None:
            album = self.database.get_album_by_id(value)
            path_text = str(album["folder_path"]) if album else path_text
            track_rows = self.database.get_tracks_for_album(value)
        self.path_label.setText(path_text)

        theme = str(QSettings("Vinqelo", "Vinqelo Player").value("appearance/theme", "vinqelo"))
        accent = {
            "vinqelo": "#438df5", "clementine": "#f59e0b",
            "amarok": "#9b6cff", "emerald": "#10b981",
            "graphite": "#94a3b8",
        }.get(theme, "#438df5")
        icon = library_folder_icon(accent)
        for row, node_kind in nodes:
            name = (
                translate_text(str(row["title"]))
                if node_kind == "album"
                else Path(row["folder_path"]).name
            )
            item = QListWidgetItem(icon, f'{name}\n{int(row["track_count"] or 0)} pistas')
            item.setData(Qt.ItemDataRole.UserRole, (node_kind, int(row["id"])))
            item.setData(Qt.ItemDataRole.UserRole + 1, dict(row))
            item.setToolTip(str(row["folder_path"]))
            self.folders.addItem(item)
        for index, row in enumerate(track_rows):
            duration = int(float(row["duration"] or 0))
            artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
            item = QTreeWidgetItem([
                str(row["track_number"] or index + 1), row["title"], artist or "",
                f"{duration // 60}:{duration % 60:02d}", row["file_format"],
            ])
            context = {
                "artist_id": int(row["artist_id"]), "album_id": value,
                "is_compilation": bool(row["is_compilation"]), "file_path": row["file_path"],
            }
            item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(track_rows, index, context))
            item.setData(0, Qt.ItemDataRole.UserRole + 1, _queue([row])[0])
            source = Path(str(row["file_path"]))
            item.setToolTip(1, f"{source.parent.name} / {source.name}")
            self.tracks.addTopLevelItem(item)
        self.folders.setVisible(bool(nodes))
        self.track_heading.setVisible(bool(track_rows))
        self.tracks.setVisible(bool(track_rows))
        self._apply_filter()
        mark_playing_track(self.tracks, self._playing_file, title_column=1)

    def _open_folder(self, item: QListWidgetItem) -> None:
        kind, value = item.data(Qt.ItemDataRole.UserRole)
        self.search.clear()
        self._display(str(kind), int(value))

    def _go_back(self) -> None:
        if not self._history:
            return
        level = self._history.pop()
        self.search.clear()
        self._display(*level, remember=False)
        self.back_button.setEnabled(bool(self._history))

    def _apply_filter(self) -> None:
        query = self.search.text().strip().casefold()
        for index in range(self.folders.count()):
            item = self.folders.item(index)
            item.setHidden(bool(query and query not in item.text().casefold()))
        for index in range(self.tracks.topLevelItemCount()):
            item = self.tracks.topLevelItem(index)
            text = " ".join(item.text(column) for column in range(self.tracks.columnCount()))
            item.setHidden(bool(query and query not in text.casefold()))

    def _play_track(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if payload:
            self.play_requested.emit(payload)

    def _folder_menu(self, position: object) -> None:
        item = self.folders.itemAt(position)
        if item is None:
            return
        self.folders.setCurrentItem(item)
        kind, value = item.data(Qt.ItemDataRole.UserRole)
        row = item.data(Qt.ItemDataRole.UserRole + 1) or {}
        menu = QMenu(self)
        play = menu.addAction("Reproducir carpeta completa")
        classify = online = None
        if kind == "artist":
            classify = menu.addAction("Marcar como compilación")
        elif kind == "album":
            menu.addSeparator()
            classify = menu.addAction(
                "Marcar como álbum normal" if row.get("is_compilation") else "Marcar como compilación"
            )
            online = menu.addAction("Buscar datos del álbum en internet…")
        selected = menu.exec(self.folders.viewport().mapToGlobal(position))
        if selected == play:
            getters = {
                "root": self.database.get_tracks_for_root,
                "artist": self.database.get_tracks_for_artist,
                "album": self.database.get_tracks_for_album,
            }
            tracks = getters[str(kind)](int(value))
            if tracks:
                self.play_requested.emit(_play_payload(tracks))
        elif selected == classify:
            if kind == "artist":
                self.database.set_artist_compilation(int(value), True)
            else:
                self.database.set_album_compilation(int(value), not bool(row.get("is_compilation")))
            self.refresh()
            self.classification_changed.emit()
        elif selected == online:
            dialog = AlbumMetadataDialog(self.database, int(value), self)
            dialog.metadata_applied.connect(self._album_metadata_applied)
            dialog.exec()

    def _track_menu(self, position: object) -> None:
        item = self.tracks.itemAt(position)
        if item is None:
            return
        self.tracks.setCurrentItem(item)
        track = item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
        file_path = str(track.get("file_path", ""))
        menu = QMenu(self)
        enqueue = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        menu.addSeparator()
        edit = menu.addAction("Editar título de la pista…")
        selected = menu.exec(self.tracks.viewport().mapToGlobal(position))
        if selected == enqueue:
            self.enqueue_requested.emit(track)
        elif selected == playlist:
            self.playlist_requested.emit(track)
        elif selected == edit:
            row = self.database.get_track_by_path(file_path)
            if row is None:
                return
            title, accepted = QInputDialog.getText(self, "Editar título", "Título de la pista:", text=row["title"])
            if accepted and title.strip():
                try:
                    new_path = self.database.update_track_title(file_path, title)
                    self.refresh()
                    self.metadata_changed.emit({file_path: new_path})
                except Exception as exc:
                    QMessageBox.warning(self, "No se pudo editar", str(exc))

    def _album_metadata_applied(self, renamed: object) -> None:
        self.refresh()
        self.metadata_changed.emit(renamed)

    def locate(self, album_id: int | None, file_path: str) -> bool:
        if album_id is None:
            return False
        self._history.clear()
        self._display("album", int(album_id), remember=False)
        for index in range(self.tracks.topLevelItemCount()):
            item = self.tracks.topLevelItem(index)
            track = item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
            if track.get("file_path") == file_path:
                self.tracks.setCurrentItem(item)
                self.tracks.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)
                return True
        return False

    def mark_playing(self, file_path: str) -> bool:
        return mark_playing_track(self.tracks, file_path, title_column=1)

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.tracks, file_path, title_column=1)
