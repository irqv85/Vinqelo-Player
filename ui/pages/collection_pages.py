"""Vistas navegables para artistas, álbumes, compilaciones y carpetas."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QMenu,
    QScrollArea,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from config import ASSETS_DIR
from database.manager import DatabaseManager
from library.artist_art import (
    ArtistCollageService,
    artist_thumbnail_path,
    collage_cache_files,
)
from library.cover_art import cover_cache_path
from library.manual_art import (
    manual_artist_image_path,
    read_image,
    save_manual_album_data,
    save_manual_album_cover,
    save_manual_artist_data,
    save_manual_artist_image,
)
from ui.artwork_dialog import choose_artwork, show_artwork
from ui.album_metadata_dialog import AlbumMetadataDialog
from ui.online_artwork_dialog import choose_online_artwork
from ui.icons import navigation_icon


def _queue(tracks: list[object]) -> list[dict[str, str]]:
    return [
        {
            "file_path": row["file_path"],
            "artist": (
                row["track_artist"]
                if row["is_compilation"]
                else (row["artist_name"] or row["track_artist"])
            ),
            "album": row["album_title"],
            "title": row["title"],
        }
        for row in tracks
    ]


def _duration(seconds: float) -> str:
    total = max(0, int(seconds or 0))
    return f"{total // 60}:{total % 60:02d}"


def _total_duration(seconds: float) -> str:
    minutes = max(0, round(float(seconds or 0) / 60))
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60} h {minutes % 60:02d} min"


def _play_payload(
    tracks: list[object], start_index: int = 0, context: dict[str, object] | None = None
) -> dict[str, object]:
    return {
        "items": _queue(tracks),
        "start_index": start_index,
        "context": context or {},
    }


def _track_item(row: object, *, folder_columns: bool = False) -> QTreeWidgetItem:
    if folder_columns:
        values = [row["title"], row["file_path"], row["file_format"], _duration(row["duration"]), ""]
    else:
        values = [str(row["track_number"] or ""), row["title"], row["track_artist"], _duration(row["duration"]), row["file_format"]]
    item = QTreeWidgetItem(values)
    item.setData(0, Qt.ItemDataRole.UserRole, _queue([row]))
    item.setData(0, Qt.ItemDataRole.UserRole + 1, _queue([row])[0])
    item.setToolTip(1, row["file_path"])
    return item


def mark_playing_track(
    tree: QTreeWidget, file_path: str, *, title_column: int = 1
) -> bool:
    """Resalta la pista activa sin alterar la posición visible del usuario."""
    scroll_bar = tree.verticalScrollBar()
    scroll_position = scroll_bar.value()
    active_item: QTreeWidgetItem | None = None
    iterator = QTreeWidgetItemIterator(tree)
    row_index = 0
    while iterator.value() is not None:
        item = iterator.value()
        track = item.data(0, Qt.ItemDataRole.UserRole + 1) or {}
        active = isinstance(track, dict) and track.get("file_path") == file_path
        font = item.font(title_column)
        font.setBold(active)
        item.setFont(title_column, font)
        item.setForeground(
            title_column,
            QBrush(QColor("#ffffff")) if active else QBrush(),
        )
        for column in range(tree.columnCount()):
            item.setBackground(
                column,
                QBrush(
                    QColor(
                        "#154f86"
                        if active
                        else ("#0b1424" if row_index % 2 == 0 else "#0e1a2d")
                    )
                ),
            )
        if active:
            active_item = item
        row_index += 1
        iterator += 1
    if active_item is not None:
        tree.setCurrentItem(active_item)
        scroll_bar.setValue(scroll_position)
        QTimer.singleShot(0, lambda: scroll_bar.setValue(scroll_position))
        return True
    return False


class CollectionPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)

    def __init__(self, database: DatabaseManager, title: str, subtitle: str) -> None:
        super().__init__()
        self.database = database
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(6)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        description = QLabel(subtitle)
        description.setObjectName("pageSubtitle")
        self.tree = QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.itemDoubleClicked.connect(self._play_item)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addSpacing(12)
        layout.addWidget(self.tree, 1)

    def _play_item(self, item: QTreeWidgetItem, _column: int) -> None:
        items = item.data(0, Qt.ItemDataRole.UserRole)
        if items:
            self.play_requested.emit(items)

    def _context_menu(self, position: object) -> None:
        item = self.tree.itemAt(position)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        track = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not track:
            return
        menu = QMenu(self)
        action = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.tree.viewport().mapToGlobal(position))
        if selected == action:
            self.enqueue_requested.emit(track)
        elif selected == playlist:
            self.playlist_requested.emit(track)


class ArtistsPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)
    album_cover_ready = Signal(int, bytes)
    artwork_changed = Signal()
    primary_artist_changed = Signal(str, bytes)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._artist_items: dict[str, QListWidgetItem] = {}
        self._collage_sources: dict[str, list[QPixmap]] = {}
        self._collage_service = ArtistCollageService(self)
        self._collage_service.cover_ready.connect(self._add_collage_cover)
        self._collage_service.album_cover_ready.connect(self._set_album_cover)
        self._artwork_notify_timer = QTimer(self)
        self._artwork_notify_timer.setSingleShot(True)
        self._artwork_notify_timer.setInterval(250)
        self._artwork_notify_timer.timeout.connect(self.artwork_changed.emit)
        self._pending_thumbnail_artists: set[str] = set()
        self._thumbnail_refresh_timer = QTimer(self)
        self._thumbnail_refresh_timer.setSingleShot(True)
        self._thumbnail_refresh_timer.setInterval(300)
        self._thumbnail_refresh_timer.timeout.connect(self._flush_thumbnail_refresh)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(6)
        self.title = QLabel("Artistas")
        self.title.setObjectName("pageTitle")
        self.subtitle = QLabel("Artistas definidos por las carpetas de tu biblioteca.")
        self.subtitle.setObjectName("pageSubtitle")
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        artist_root = QWidget()
        artist_root_layout = QVBoxLayout(artist_root)
        artist_root_layout.setContentsMargins(0, 0, 0, 0)
        artist_root_layout.setSpacing(10)
        self.artist_search = QLineEdit()
        self.artist_search.setObjectName("collectionSearch")
        self.artist_search.setPlaceholderText("Buscar artistas…")
        self.artist_search.addAction(
            navigation_icon("search", "#8fa7c7"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.artist_search.textChanged.connect(self._filter_artists)
        artist_root_layout.addWidget(self.artist_search)

        self.artist_grid = QListWidget()
        self.artist_grid.setObjectName("artistGrid")
        self.artist_grid.setViewMode(QListView.ViewMode.IconMode)
        self.artist_grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.artist_grid.setMovement(QListView.Movement.Static)
        self.artist_grid.setWrapping(True)
        self.artist_grid.setSpacing(14)
        self.artist_grid.setIconSize(QSize(126, 126))
        self.artist_grid.setGridSize(QSize(166, 176))
        self.artist_grid.itemClicked.connect(self._open_artist)
        self.artist_grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.artist_grid.customContextMenuRequested.connect(self._artist_context_menu)
        artist_root_layout.addWidget(self.artist_grid, 1)
        self.stack.addWidget(artist_root)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 8, 0, 0)
        detail_header = QHBoxLayout()
        back = QPushButton("←  Artistas")
        back.setObjectName("secondaryButton")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.artist_heading = QLabel("")
        self.artist_heading.setObjectName("pageTitle")
        self.play_artist_button = QPushButton("▶  Reproducir artista")
        self.play_artist_button.setObjectName("primaryButton")
        self.play_artist_button.clicked.connect(self._play_current_artist)
        detail_header.addWidget(back)
        detail_header.addWidget(self.artist_heading, 1)
        detail_header.addWidget(self.play_artist_button)
        detail_layout.addLayout(detail_header)
        track_filter_row = QHBoxLayout()
        self.tracks_label = QLabel("ÁLBUMES Y PISTAS")
        self.tracks_label.setObjectName("columnHeader")
        self.track_search = QLineEdit()
        self.track_search.setObjectName("trackSearch")
        self.track_search.setPlaceholderText("Buscar álbum o pista de este artista…")
        self.track_search.addAction(
            navigation_icon("search", "#8fa7c7"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.track_search.setMaximumWidth(360)
        self.track_search.textChanged.connect(self._filter_tracks)
        track_filter_row.addWidget(self.tracks_label)
        track_filter_row.addStretch(1)
        track_filter_row.addWidget(self.track_search)
        detail_layout.addLayout(track_filter_row)
        self.album_scroll = QScrollArea()
        self.album_scroll.setObjectName("albumRowsScroll")
        self.album_scroll.setWidgetResizable(True)
        self.album_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.album_rows_container = QWidget()
        self.album_rows_container.setObjectName("albumRowsContainer")
        self.album_rows_layout = QVBoxLayout(self.album_rows_container)
        self.album_rows_layout.setContentsMargins(0, 0, 4, 0)
        self.album_rows_layout.setSpacing(12)
        self.album_rows_layout.addStretch(1)
        self.album_scroll.setWidget(self.album_rows_container)
        detail_layout.addWidget(self.album_scroll, 1)
        # Se conservan como modelos internos para compatibilidad con la lógica
        # existente de carátulas; la presentación visible usa filas horizontales.
        self.album_grid = QListWidget(self)
        self.album_grid.hide()
        self.track_tree = QTreeWidget(self)
        self.track_tree.hide()
        self.stack.addWidget(detail)
        self._album_sections: dict[int, QFrame] = {}
        self._album_track_trees: dict[int, QTreeWidget] = {}
        self._album_cover_labels: dict[int, QLabel] = {}
        self._album_rows: dict[int, object] = {}
        self._current_artist_queue: list[dict[str, str]] = []
        self._current_artist_id = -1
        self._playing_file = ""

    def refresh(self) -> None:
        self.artist_grid.clear()
        self._artist_items.clear()
        self._collage_sources.clear()
        default = _default_pixmap(126)
        for artist in self.database.get_artists():
            thumbnail = QPixmap(str(artist_thumbnail_path(artist["name"])))
            if thumbnail.isNull():
                manual_data = read_image(manual_artist_image_path(artist["name"]))
                manual_pixmap = QPixmap()
                if manual_data:
                    manual_pixmap.loadFromData(manual_data)
                thumbnail = _circle_pixmap(
                    manual_pixmap if not manual_pixmap.isNull() else default, 126
                )
            item = QListWidgetItem(QIcon(thumbnail), artist["name"])
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            item.setData(Qt.ItemDataRole.UserRole, int(artist["id"]))
            item.setData(Qt.ItemDataRole.UserRole + 1, artist["folder_path"])
            item.setData(Qt.ItemDataRole.UserRole + 2, artist["name"])
            item.setToolTip(
                f'{artist["album_count"]} álbum(es) · {artist["track_count"]} pistas · '
                f'{_total_duration(artist["total_duration"])}'
            )
            self.artist_grid.addItem(item)
            self._artist_items[artist["name"]] = item
            self._collage_sources[artist["name"]] = []
        self._filter_artists(self.artist_search.text())

    def prepare_artist_thumbnails(
        self, artist_names: set[str] | None = None, *, force: bool = True
    ) -> int:
        """Precalcula una miniatura por artista durante la actualización manual."""
        albums_by_artist: dict[str, list[object]] = {}
        for album in self.database.get_albums(None):
            if album["is_compilation"]:
                continue
            name = str(album["artist_name"] or album["album_artist"])
            albums_by_artist.setdefault(name, []).append(album)
        prepared = 0
        for artist in self.database.get_artists():
            artist_name = str(artist["name"])
            if artist_names is not None and artist_name not in artist_names:
                continue
            destination = artist_thumbnail_path(artist_name)
            if destination.is_file() and not force:
                continue
            manual_data = read_image(manual_artist_image_path(artist_name))
            manual = QPixmap()
            if manual_data:
                manual.loadFromData(manual_data)
            if not manual.isNull():
                thumbnail = _circle_pixmap(manual, 126)
            else:
                sources: list[QPixmap] = []
                for album in albums_by_artist.get(artist_name, []):
                    candidates = [
                        cover_cache_path(album["title"], artist_name),
                        Path(album["cover_path"]) if album["cover_path"] else None,
                    ]
                    for candidate in candidates:
                        if candidate is None or not candidate.is_file():
                            continue
                        pixmap = QPixmap(str(candidate))
                        if not pixmap.isNull():
                            sources.append(pixmap)
                            break
                    if len(sources) >= 4:
                        break
                if len(sources) < 4:
                    for path in collage_cache_files(artist_name):
                        pixmap = QPixmap(str(path))
                        if not pixmap.isNull():
                            sources.append(pixmap)
                        if len(sources) >= 4:
                            break
                thumbnail = (
                    _collage_pixmap(sources[:4], 126)
                    if sources
                    else _circle_pixmap(_default_pixmap(126), 126)
                )
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                if thumbnail.save(str(destination), "PNG"):
                    prepared += 1
            except OSError:
                continue
        return prepared

    def queue_artwork_updates(self) -> None:
        """Busca portadas faltantes solo después de Actualizar biblioteca."""
        artists_with_albums: set[str] = set()
        for album in self.database.get_albums(None):
            artist_name = album["artist_name"] or album["album_artist"]
            if not album["is_compilation"] and album["title"] != "Pistas sueltas":
                artists_with_albums.add(artist_name)
            self._collage_service.request_album(
                int(album["id"]),
                album["title"],
                artist_name,
                album["cover_path"],
            )
        for artist_name in (str(row["name"]) for row in self.database.get_artists()):
            if artist_name not in artists_with_albums:
                self._collage_service.request(artist_name)

    def _filter_artists(self, text: str) -> None:
        query = text.strip().casefold()
        for index in range(self.artist_grid.count()):
            item = self.artist_grid.item(index)
            artist_name = str(item.data(Qt.ItemDataRole.UserRole + 2) or "")
            item.setHidden(bool(query) and query not in artist_name.casefold())

    def show_root(self) -> None:
        self.stack.setCurrentIndex(0)
        self.artist_search.clear()
        self.track_search.clear()
        self.artist_grid.clearSelection()
        self.artist_grid.verticalScrollBar().setValue(0)

    def _add_collage_cover(self, artist: str, data: bytes) -> None:
        if manual_artist_image_path(artist).is_file():
            return
        item = self._artist_items.get(artist)
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            sources = self._collage_sources.setdefault(artist, [])
            if len(sources) < 4:
                sources.append(pixmap)
            thumbnail = _collage_pixmap(sources, 126)
            destination = artist_thumbnail_path(artist)
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                thumbnail.save(str(destination), "PNG")
            except OSError:
                pass
            if item is not None:
                item.setIcon(QIcon(thumbnail))
            if self.artist_heading.text() == artist:
                for album_id, album in self._album_rows.items():
                    if album["title"] != "Pistas sueltas":
                        continue
                    label = self._album_cover_labels.get(album_id)
                    if label is not None:
                        label.setPixmap(
                            _album_pixmap(
                                album,
                                artist,
                                (
                                    item.icon().pixmap(150, 150)
                                    if item is not None
                                    else thumbnail
                                ),
                            ).scaled(
                                150,
                                150,
                                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
            self._artwork_notify_timer.start()

    def _artist_context_menu(self, position: object) -> None:
        item = self.artist_grid.itemAt(position)
        if item is None:
            return
        artist_name = str(item.data(Qt.ItemDataRole.UserRole + 2) or item.text())
        self.artist_grid.setCurrentItem(item)
        menu = QMenu(self)
        play_all = menu.addAction("Reproducir todos los álbumes")
        menu.addSeparator()
        online = menu.addAction("Buscar foto en internet…")
        choose = menu.addAction("Buscar una foto en el equipo…")
        preview = menu.addAction("Ver foto en grande")
        selected = menu.exec(self.artist_grid.viewport().mapToGlobal(position))
        if selected == play_all:
            artist_id = int(item.data(Qt.ItemDataRole.UserRole))
            tracks = self.database.get_tracks_for_artist(artist_id)
            if tracks:
                self.play_requested.emit(
                    _play_payload(tracks, context={"artist_id": artist_id})
                )
        elif selected == preview:
            data = read_image(manual_artist_image_path(artist_name))
            pixmap = QPixmap()
            if data:
                pixmap.loadFromData(data)
            if pixmap.isNull():
                pixmap = item.icon().pixmap(512, 512)
            show_artwork(self, artist_name, pixmap)
        elif selected in (online, choose):
            online_data = (
                choose_online_artwork(self, artist_name, kind="artist")
                if selected == online
                else None
            )
            source = (
                choose_artwork(self, f"Elegir foto de {artist_name}")
                if selected == choose
                else None
            )
            if selected == choose and source is None:
                return
            if selected == online and online_data is None:
                return
            try:
                data = (
                    save_manual_artist_data(artist_name, online_data)
                    if online_data is not None
                    else save_manual_artist_image(artist_name, source)
                )
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "No se pudo guardar", str(exc))
                return
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            thumbnail = _circle_pixmap(pixmap, 126)
            item.setIcon(QIcon(thumbnail))
            destination = artist_thumbnail_path(artist_name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            thumbnail.save(str(destination), "PNG")
            if self.artist_heading.text() == artist_name:
                for label in self._album_cover_labels.values():
                    label.setPixmap(
                        pixmap.scaled(
                            150,
                            150,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
            self.primary_artist_changed.emit(artist_name, data)
            self.artwork_changed.emit()

    def _album_context_menu(self, position: object) -> None:
        item = self.album_grid.itemAt(position)
        if item is None:
            return
        self.album_grid.setCurrentItem(item)
        menu = QMenu(self)
        online = menu.addAction("Buscar carátula en internet…")
        choose = menu.addAction("Buscar una carátula en el equipo…")
        preview = menu.addAction("Ver carátula en grande")
        selected = menu.exec(self.album_grid.viewport().mapToGlobal(position))
        if selected == preview:
            show_artwork(self, item.text(), item.icon().pixmap(512, 512))
        elif selected in (online, choose):
            album_id = int(item.data(Qt.ItemDataRole.UserRole))
            album = next(
                row
                for row in self.database.get_albums_for_artist(self._current_artist_id)
                if int(row["id"]) == album_id
            )
            artist = album["artist_name"] or album["album_artist"]
            online_data = (
                choose_online_artwork(
                    self, album["title"], kind="album", artist=artist
                )
                if selected == online
                else None
            )
            source = (
                choose_artwork(self, f"Elegir carátula de {item.text()}")
                if selected == choose
                else None
            )
            if online_data is None and source is None:
                return
            try:
                data = (
                    save_manual_album_data(album["title"], artist, online_data)
                    if online_data is not None
                    else save_manual_album_cover(album["title"], artist, source)
                )
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "No se pudo guardar", str(exc))
                return
            self._set_album_cover(album_id, data)

    def _set_album_cover(self, album_id: int, data: bytes) -> None:
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        display_pixmap = pixmap
        for index in range(self.album_grid.count()):
            item = self.album_grid.item(index)
            if int(item.data(Qt.ItemDataRole.UserRole)) == album_id:
                item.setIcon(QIcon(display_pixmap))
                break
        label = self._album_cover_labels.get(album_id)
        if label is not None:
            label.setPixmap(
                display_pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.album_cover_ready.emit(album_id, data)
        album = self.database.get_album_by_id(album_id)
        if album is not None:
            artist_name = str(album["artist_name"] or album["album_artist"])
            self._pending_thumbnail_artists.add(artist_name)
            self._thumbnail_refresh_timer.start()
        self.artwork_changed.emit()

    def _flush_thumbnail_refresh(self) -> None:
        artists = set(self._pending_thumbnail_artists)
        self._pending_thumbnail_artists.clear()
        if not artists:
            return
        self.prepare_artist_thumbnails(artists, force=True)
        for artist in artists:
            item = self._artist_items.get(artist)
            pixmap = QPixmap(str(artist_thumbnail_path(artist)))
            if item is not None and not pixmap.isNull():
                item.setIcon(QIcon(pixmap))

    def _open_artist(self, item: QListWidgetItem) -> None:
        artist_id = int(item.data(Qt.ItemDataRole.UserRole))
        artist_name = str(item.data(Qt.ItemDataRole.UserRole + 2) or item.text())
        self._current_artist_id = artist_id
        self.artist_heading.setText(artist_name)
        artist_tracks = self.database.get_tracks_for_artist(artist_id)
        self._current_artist_queue = _queue(artist_tracks)
        artist_duration = sum(float(track["duration"] or 0) for track in artist_tracks)
        self.tracks_label.setText(
            f"ÁLBUMES Y PISTAS · {len(artist_tracks)} pistas · "
            f"{_total_duration(artist_duration)}"
        )
        self._clear_album_rows()
        self.album_grid.clear()
        albums = self.database.get_albums_for_artist(artist_id)
        for album in albums:
            tracks = self.database.get_tracks_for_album(album["id"])
            album_icon = (
                QIcon(_album_pixmap(album, artist_name, item.icon().pixmap(150, 150)))
            )
            album_item = QListWidgetItem(
                album_icon, album["title"]
            )
            album_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            album_item.setData(Qt.ItemDataRole.UserRole, int(album["id"]))
            context = {
                "artist_id": artist_id,
                "album_id": int(album["id"]),
                "is_compilation": bool(album["is_compilation"]),
            }
            album_item.setData(
                Qt.ItemDataRole.UserRole + 1, _play_payload(tracks, context=context)
            )
            album_item.setToolTip(
                f'{album["track_count"]} pistas · {_total_duration(album["total_duration"])}'
            )
            self.album_grid.addItem(album_item)
            self._build_album_row(album, tracks, item, artist_name)
        self.play_artist_button.setText(
            "▶  Reproducir todos los álbumes"
            if len(albums) > 1
            else "▶  Reproducir artista"
        )
        self.stack.setCurrentIndex(1)
        self.album_scroll.verticalScrollBar().setValue(0)
        if self._playing_file:
            self.set_playing_file(self._playing_file)

    def open_artist(self, artist_id: int) -> bool:
        item = next(
            (
                self.artist_grid.item(index)
                for index in range(self.artist_grid.count())
                if int(self.artist_grid.item(index).data(Qt.ItemDataRole.UserRole))
                == int(artist_id)
            ),
            None,
        )
        if item is None:
            return False
        self.artist_grid.setCurrentItem(item)
        self._open_artist(item)
        return True

    def _clear_album_rows(self) -> None:
        while self.album_rows_layout.count() > 1:
            layout_item = self.album_rows_layout.takeAt(0)
            widget = layout_item.widget()
            if widget is not None:
                widget.deleteLater()
        self._album_sections.clear()
        self._album_track_trees.clear()
        self._album_cover_labels.clear()
        self._album_rows.clear()

    def _build_album_row(
        self,
        album: object,
        tracks: list[object],
        artist_item: QListWidgetItem,
        artist_name: str,
    ) -> None:
        album_id = int(album["id"])
        row = QFrame()
        row.setObjectName("artistAlbumRow")
        row.setProperty("albumId", album_id)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(13, 13, 13, 13)
        row_layout.setSpacing(16)

        artwork_box = QWidget()
        artwork_box.setFixedWidth(164)
        artwork_layout = QVBoxLayout(artwork_box)
        artwork_layout.setContentsMargins(0, 0, 0, 0)
        artwork_layout.setSpacing(6)
        cover = QLabel()
        cover.setObjectName("artistAlbumCover")
        cover.setFixedSize(150, 150)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = _album_pixmap(
            album, artist_name, artist_item.icon().pixmap(150, 150)
        )
        if not pixmap.isNull():
            cover.setPixmap(
                pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        cover.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        cover.customContextMenuRequested.connect(
            lambda position, active_id=album_id, active_cover=cover:
            self._album_row_context_menu(active_id, active_cover, position)
        )
        album_title = QLabel(str(album["title"]))
        album_title.setObjectName("artistAlbumTitle")
        album_title.setWordWrap(True)
        album_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        metadata = QLabel(
            f'{len(tracks)} pistas · {_total_duration(album["total_duration"])}'
        )
        metadata.setObjectName("mutedLabel")
        metadata.setAlignment(Qt.AlignmentFlag.AlignCenter)
        play_album = QPushButton("▶  Reproducir álbum")
        play_album.setObjectName("secondaryButton")
        play_album.clicked.connect(
            lambda _checked=False, active_tracks=tracks, active_id=album_id:
            self.play_requested.emit(
                _play_payload(
                    active_tracks,
                    context={
                        "artist_id": self._current_artist_id,
                        "album_id": active_id,
                        "is_compilation": False,
                    },
                )
            )
        )
        artwork_layout.addWidget(cover)
        artwork_layout.addWidget(album_title)
        artwork_layout.addWidget(metadata)
        artwork_layout.addWidget(play_album)
        artwork_layout.addStretch(1)

        list_box = QWidget()
        list_layout = QVBoxLayout(list_box)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(6)
        list_title = QLabel("LISTA DE TEMAS")
        list_title.setObjectName("columnHeader")
        tree = QTreeWidget()
        tree.setObjectName("artistAlbumTracks")
        tree.setHeaderLabels(["#", "TÍTULO", "ARTISTA", "DURACIÓN", "TIPO"])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        tree.setColumnWidth(0, 42)
        tree.setColumnWidth(1, 340)
        tree.setColumnWidth(2, 190)
        tree.setColumnWidth(3, 90)
        tree.itemDoubleClicked.connect(self._play_track)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(
            lambda position, active_tree=tree:
            self._album_track_context_menu(active_tree, position)
        )
        for index, track in enumerate(tracks):
            track_item = _track_item(track)
            track_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                _play_payload(
                    tracks,
                    index,
                    {
                        "artist_id": self._current_artist_id,
                        "album_id": album_id,
                        "is_compilation": bool(track["is_compilation"]),
                        "file_path": track["file_path"],
                    },
                ),
            )
            tree.addTopLevelItem(track_item)
        tree.setFixedHeight(max(145, min(500, 38 + len(tracks) * 31)))
        list_layout.addWidget(list_title)
        list_layout.addWidget(tree)
        row_layout.addWidget(artwork_box)
        row_layout.addWidget(list_box, 1)
        self.album_rows_layout.insertWidget(self.album_rows_layout.count() - 1, row)
        self._album_sections[album_id] = row
        self._album_track_trees[album_id] = tree
        self._album_cover_labels[album_id] = cover
        self._album_rows[album_id] = album

    def _album_track_context_menu(self, tree: QTreeWidget, position: object) -> None:
        item = tree.itemAt(position)
        if item is None:
            return
        tree.setCurrentItem(item)
        menu = QMenu(self)
        enqueue = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(tree.viewport().mapToGlobal(position))
        track = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if selected == enqueue:
            self.enqueue_requested.emit(track)
        elif selected == playlist:
            self.playlist_requested.emit(track)

    def _album_row_context_menu(
        self, album_id: int, cover: QLabel, position: object
    ) -> None:
        album = self._album_rows.get(album_id)
        if album is None:
            return
        menu = QMenu(self)
        online = menu.addAction("Buscar carátula en internet…")
        choose = menu.addAction("Buscar una carátula en el equipo…")
        preview = menu.addAction("Ver carátula en grande")
        selected = menu.exec(cover.mapToGlobal(position))
        if selected == preview:
            show_artwork(
                self,
                str(album["title"]),
                cover.pixmap() if cover.pixmap() else QPixmap(),
            )
            return
        if selected not in (online, choose):
            return
        artist = album["artist_name"] or album["album_artist"]
        online_data = (
            choose_online_artwork(
                self, album["title"], kind="album", artist=artist
            )
            if selected == online
            else None
        )
        source = (
            choose_artwork(self, f'Buscar carátula de {album["title"]}')
            if selected == choose
            else None
        )
        if online_data is None and source is None:
            return
        try:
            data = (
                save_manual_album_data(album["title"], artist, online_data)
                if online_data is not None
                else save_manual_album_cover(album["title"], artist, source)
            )
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))
            return
        self._set_album_cover(album_id, data)

    def _show_album_tracks(self, item: QListWidgetItem) -> None:
        self.track_search.clear()
        self.track_tree.clear()
        album_id = int(item.data(Qt.ItemDataRole.UserRole))
        tracks = self.database.get_tracks_for_album(album_id)
        album_duration = sum(float(track["duration"] or 0) for track in tracks)
        self.tracks_label.setText(
            f"PISTAS DEL ÁLBUM · {len(tracks)} pistas · "
            f"{_total_duration(album_duration)}"
        )
        for index, row in enumerate(tracks):
            track_item = _track_item(row)
            track_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                _play_payload(
                    tracks,
                    index,
                    {
                        "artist_id": self._current_artist_id,
                        "album_id": album_id,
                        "is_compilation": bool(row["is_compilation"]),
                        "file_path": row["file_path"],
                    },
                ),
            )
            self.track_tree.addTopLevelItem(track_item)
        if self._playing_file:
            mark_playing_track(self.track_tree, self._playing_file)

    def _filter_tracks(self, text: str) -> None:
        query = text.strip().casefold()
        for album_id, tree in self._album_track_trees.items():
            album = self._album_rows.get(album_id)
            album_matches = bool(
                album
                and query
                and query in str(album["title"]).casefold()
            )
            visible_tracks = 0
            for index in range(tree.topLevelItemCount()):
                item = tree.topLevelItem(index)
                searchable = " ".join(
                    item.text(column) for column in (1, 2)
                ).casefold()
                hidden = bool(query) and not album_matches and query not in searchable
                item.setHidden(hidden)
                if not hidden:
                    visible_tracks += 1
            section = self._album_sections.get(album_id)
            if section is not None:
                section.setVisible(not query or album_matches or visible_tracks > 0)

    def _play_current_artist(self) -> None:
        if self._current_artist_queue:
            self.play_requested.emit(
                {
                    "items": self._current_artist_queue,
                    "start_index": 0,
                    "context": {"artist_id": self._current_artist_id},
                }
            )

    def _play_album(self, item: QListWidgetItem) -> None:
        payload = item.data(Qt.ItemDataRole.UserRole + 1)
        if payload:
            self.play_requested.emit(payload)

    def _play_track(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if payload:
            self.play_requested.emit(payload)

    def _track_context_menu(self, position: object) -> None:
        item = self.track_tree.itemAt(position)
        if item is None:
            return
        self.track_tree.setCurrentItem(item)
        menu = QMenu(self)
        action = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.track_tree.viewport().mapToGlobal(position))
        if selected == action:
            self.enqueue_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))
        elif selected == playlist:
            self.playlist_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))

    def locate(self, artist_id: int, album_id: int | None, file_path: str) -> bool:
        if not self.open_artist(artist_id):
            return False
        trees = (
            [(album_id, self._album_track_trees.get(album_id))]
            if album_id is not None
            else list(self._album_track_trees.items())
        )
        for active_album_id, tree in trees:
            if tree is None:
                continue
            for index in range(tree.topLevelItemCount()):
                track_item = tree.topLevelItem(index)
                payload = track_item.data(0, Qt.ItemDataRole.UserRole) or {}
                context = payload.get("context", {}) if isinstance(payload, dict) else {}
                if context.get("file_path") != file_path:
                    continue
                tree.setCurrentItem(track_item)
                tree.scrollToItem(track_item)
                section = self._album_sections.get(int(active_album_id))
                if section is not None:
                    self.album_scroll.ensureWidgetVisible(section, 0, 24)
                return True
        return True

    def mark_playing(self, file_path: str) -> bool:
        marked = False
        for tree in self._album_track_trees.values():
            marked = mark_playing_track(tree, file_path) or marked
        return marked

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        self.mark_playing(file_path)


class AlbumsPage(CollectionPage):
    def __init__(self, database: DatabaseManager, *, compilations: bool = False) -> None:
        self.compilations = compilations
        super().__init__(database, "Compilaciones" if compilations else "Álbumes", "Doble clic para reproducir la colección completa.")
        self.tree.setHeaderLabels(["#", "ÁLBUM / PISTA", "ARTISTA", "DURACIÓN", "TIPO"])

    def refresh(self) -> None:
        self.tree.clear()
        for album in self.database.get_albums(self.compilations):
            tracks = self.database.get_tracks_for_album(album["id"])
            album_item = QTreeWidgetItem(["", album["title"], album["artist_name"] or album["album_artist"], "", f'{album["track_count"]} pistas'])
            context = {
                "artist_id": album["artist_id"], "album_id": album["id"],
                "is_compilation": bool(album["is_compilation"]),
            }
            album_item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(tracks, context=context))
            for index, track in enumerate(tracks):
                track_item = _track_item(track)
                track_item.setData(
                    0, Qt.ItemDataRole.UserRole,
                    _play_payload(tracks, index, {**context, "file_path": track["file_path"]}),
                )
                album_item.addChild(track_item)
            self.tree.addTopLevelItem(album_item)
        self.tree.setColumnWidth(1, 360)

    def locate(self, album_id: int | None, file_path: str) -> bool:
        for top_index in range(self.tree.topLevelItemCount()):
            album_item = self.tree.topLevelItem(top_index)
            payload = album_item.data(0, Qt.ItemDataRole.UserRole) or {}
            context = payload.get("context", {}) if isinstance(payload, dict) else {}
            if album_id is not None and context.get("album_id") != album_id:
                continue
            album_item.setExpanded(True)
            self.tree.setCurrentItem(album_item)
            for child_index in range(album_item.childCount()):
                child = album_item.child(child_index)
                child_payload = child.data(0, Qt.ItemDataRole.UserRole) or {}
                child_context = (
                    child_payload.get("context", {})
                    if isinstance(child_payload, dict)
                    else {}
                )
                if child_context.get("file_path") == file_path:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    return True
            return True
        return False


class FoldersPage(CollectionPage):
    metadata_changed = Signal(object)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__(database, "Carpetas", "Navega la estructura física y reproduce cualquier nivel con doble clic.")
        self._playing_file = ""
        self.tree.setHeaderLabels(["CARPETA / PISTA", "RUTA / ARTISTA", "TIPO", "DURACIÓN", "PISTAS"])

    def refresh(self) -> None:
        self.tree.clear()
        for root in self.database.get_roots():
            root_path = Path(root["folder_path"])
            root_tracks = self.database.get_tracks_for_root(root["id"])
            root_item = QTreeWidgetItem([
                root_path.name, str(root_path), "Raíz",
                _total_duration(root["total_duration"]), str(root["track_count"]),
            ])
            root_item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(root_tracks))
            for artist in self.database.get_artists_for_root(root["id"]):
                artist_tracks = self.database.get_tracks_for_artist(artist["id"])
                artist_item = QTreeWidgetItem([
                    Path(artist["folder_path"]).name, artist["name"], "Artista",
                    _total_duration(artist["total_duration"]), str(artist["track_count"]),
                ])
                artist_item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(artist_tracks, context={"artist_id": artist["id"]}))
                for album in self.database.get_albums_for_artist(artist["id"]):
                    album_tracks = self.database.get_tracks_for_album(album["id"])
                    album_item = QTreeWidgetItem([
                        album["title"], artist["name"],
                        "Compilación" if album["is_compilation"] else "Álbum",
                        _total_duration(album["total_duration"]), str(album["track_count"]),
                    ])
                    context = {"artist_id": artist["id"], "album_id": album["id"], "is_compilation": bool(album["is_compilation"])}
                    album_item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(album_tracks, context=context))
                    for index, track in enumerate(album_tracks):
                        track_item = _track_item(track, folder_columns=True)
                        track_item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(album_tracks, index, {**context, "file_path": track["file_path"]}))
                        album_item.addChild(track_item)
                    artist_item.addChild(album_item)
                root_item.addChild(artist_item)
            self.tree.addTopLevelItem(root_item)
        if self._playing_file:
            mark_playing_track(self.tree, self._playing_file, title_column=0)

    def _context_menu(self, position: object) -> None:
        item = self.tree.itemAt(position)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        payload = item.data(0, Qt.ItemDataRole.UserRole) or {}
        context = payload.get("context", {}) if isinstance(payload, dict) else {}
        file_path = str(context.get("file_path", ""))
        album_id = context.get("album_id")
        menu = QMenu(self)
        enqueue = playlist = edit = online = None
        if file_path:
            enqueue = menu.addAction("Añadir a la cola")
            playlist = menu.addAction("Añadir a lista de reproducción…")
            menu.addSeparator()
            edit = menu.addAction("Editar título de la pista…")
        elif album_id is not None:
            online = menu.addAction("Buscar datos del álbum en internet…")
        else:
            return
        selected = menu.exec(self.tree.viewport().mapToGlobal(position))
        track = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if selected == enqueue and track:
            self.enqueue_requested.emit(track)
        elif selected == playlist and track:
            self.playlist_requested.emit(track)
        elif selected == edit:
            row = self.database.get_track_by_path(file_path)
            if row is None:
                return
            title, accepted = QInputDialog.getText(
                self, "Editar título", "Título de la pista:", text=row["title"]
            )
            if not accepted or not title.strip():
                return
            try:
                new_path = self.database.update_track_title(file_path, title)
                self.refresh()
                self.metadata_changed.emit({file_path: new_path})
            except Exception as exc:
                QMessageBox.warning(self, "No se pudo editar", str(exc))
        elif selected == online:
            dialog = AlbumMetadataDialog(self.database, int(album_id), self)
            dialog.metadata_applied.connect(self._album_metadata_applied)
            dialog.exec()

    def _album_metadata_applied(self, renamed: object) -> None:
        self.refresh()
        self.metadata_changed.emit(renamed)

    def show_root(self) -> None:
        self.tree.collapseAll()
        self.tree.clearSelection()
        self.tree.verticalScrollBar().setValue(0)

    def locate(self, album_id: int | None, file_path: str) -> bool:
        def visit(item: QTreeWidgetItem) -> bool:
            payload = item.data(0, Qt.ItemDataRole.UserRole) or {}
            context = payload.get("context", {}) if isinstance(payload, dict) else {}
            if (
                context.get("file_path") == file_path
                and (album_id is None or context.get("album_id") == album_id)
            ):
                parent = item.parent()
                while parent is not None:
                    parent.setExpanded(True)
                    parent = parent.parent()
                self.tree.setCurrentItem(item)
                self.tree.scrollToItem(item)
                return True
            for index in range(item.childCount()):
                if visit(item.child(index)):
                    return True
            return False

        return any(
            visit(self.tree.topLevelItem(index))
            for index in range(self.tree.topLevelItemCount())
        )

    def mark_playing(self, file_path: str) -> bool:
        return mark_playing_track(self.tree, file_path, title_column=0)

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.tree, file_path, title_column=0)
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 390)


def _default_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(str(ASSETS_DIR / "icons" / "vinqelo-v.png"))
    return pixmap if not pixmap.isNull() else QPixmap(size, size)


def _circle_pixmap(source: QPixmap, size: int) -> QPixmap:
    return _collage_pixmap([source], size)


def _collage_pixmap(sources: list[QPixmap], size: int) -> QPixmap:
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#17243b"))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    path = QPainterPath()
    path.addEllipse(1, 1, size - 2, size - 2)
    painter.setClipPath(path)
    if len(sources) <= 1:
        rectangles = [QRectF(0, 0, size, size)]
    elif len(sources) == 2:
        rectangles = [QRectF(0, 0, size / 2, size), QRectF(size / 2, 0, size / 2, size)]
    else:
        half = size / 2
        rectangles = [
            QRectF(0, 0, half, half), QRectF(half, 0, half, half),
            QRectF(0, half, half, half), QRectF(half, half, half, half),
        ]
    for source, rectangle in zip(sources[:4], rectangles):
        scaled = source.scaled(
            int(rectangle.width()),
            int(rectangle.height()),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.save()
        painter.setClipRect(rectangle, Qt.ClipOperation.IntersectClip)
        painter.drawPixmap(
            int(rectangle.x() + (rectangle.width() - scaled.width()) / 2),
            int(rectangle.y() + (rectangle.height() - scaled.height()) / 2),
            scaled,
        )
        painter.restore()
    painter.end()
    return result


def _album_pixmap(
    album: object, artist: str, fallback: QPixmap | None = None
) -> QPixmap:
    cache = cover_cache_path(album["title"], artist)
    candidates = [cache, Path(album["cover_path"]) if album["cover_path"] else None]
    for path in candidates:
        if path and path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap
    primary = _primary_artist_pixmap(artist)
    if not primary.isNull():
        return primary
    if fallback is not None and not fallback.isNull():
        return fallback
    return _default_pixmap(108)


def _primary_artist_pixmap(artist: str) -> QPixmap:
    data = read_image(manual_artist_image_path(artist))
    pixmap = QPixmap()
    if data:
        pixmap.loadFromData(data)
    return pixmap
