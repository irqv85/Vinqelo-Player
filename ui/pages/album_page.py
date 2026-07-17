"""Cuadrícula visual de álbumes y compilaciones."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem,
    QLineEdit, QMenu, QMessageBox, QPushButton, QStackedWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from database.manager import DatabaseManager
from library.manual_art import save_manual_album_cover, save_manual_album_data
from ui.artwork_dialog import choose_artwork, show_artwork
from ui.online_artwork_dialog import choose_online_artwork
from ui.icons import navigation_icon
from ui.pages.collection_pages import (
    _album_pixmap,
    _play_payload,
    _queue,
    _track_item,
    _primary_artist_pixmap,
    _total_duration,
    mark_playing_track,
)


class AlbumGridPage(QWidget):
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)
    manual_cover_selected = Signal(int, bytes)

    def __init__(self, database: DatabaseManager, *, compilations: bool = False) -> None:
        super().__init__()
        self.database = database
        self.compilations = compilations
        self._album_items: dict[int, QListWidgetItem] = {}
        self._album_rows: dict[int, object] = {}
        self._current_album_id = -1
        self._playing_file = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        title = QLabel("Compilaciones" if compilations else "Álbumes")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Portadas organizadas por las carpetas de tu biblioteca.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        grid_page = QWidget()
        grid_layout = QVBoxLayout(grid_page)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(10)
        self.collection_search = QLineEdit()
        self.collection_search.setObjectName("collectionSearch")
        collection_name = "compilaciones" if compilations else "álbumes"
        self.collection_search.setPlaceholderText(f"Buscar {collection_name}…")
        self.collection_search.addAction(
            navigation_icon("search", "#8fa7c7"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.collection_search.textChanged.connect(self._filter_collections)
        grid_layout.addWidget(self.collection_search)

        self.grid = QListWidget()
        self.grid.setObjectName("visualAlbumGrid")
        self.grid.setViewMode(QListView.ViewMode.IconMode)
        self.grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid.setMovement(QListView.Movement.Static)
        self.grid.setWrapping(True)
        self.grid.setSpacing(10)
        self.grid.setGridSize(QSize(180, 238))
        self.grid.itemClicked.connect(self._open_album)
        self.grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._album_context_menu)
        grid_layout.addWidget(self.grid, 1)
        self.stack.addWidget(grid_page)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(0, 4, 0, 0)
        header = QHBoxLayout()
        back = QPushButton("←  Volver")
        back.setObjectName("secondaryButton")
        back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        heading_box = QVBoxLayout()
        self.album_heading = QLabel("")
        self.album_heading.setObjectName("pageTitle")
        self.artist_heading = QLabel("")
        self.artist_heading.setObjectName("pageSubtitle")
        heading_box.addWidget(self.album_heading)
        heading_box.addWidget(self.artist_heading)
        play = QPushButton("▶  Reproducir álbum")
        play.setObjectName("primaryButton")
        play.clicked.connect(self._play_album)
        header.addWidget(back)
        header.addLayout(heading_box, 1)
        header.addWidget(play)
        detail_layout.addLayout(header)
        self.track_search = QLineEdit()
        self.track_search.setObjectName("trackSearch")
        self.track_search.setPlaceholderText("Buscar dentro de este álbum…")
        self.track_search.addAction(
            navigation_icon("search", "#8fa7c7"),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.track_search.textChanged.connect(self._filter_tracks)
        detail_layout.addWidget(self.track_search)
        self.tracks = QTreeWidget()
        self.tracks.setHeaderLabels(["#", "TÍTULO", "ARTISTA", "DURACIÓN", "TIPO"])
        self.tracks.setRootIsDecorated(False)
        self.tracks.setAlternatingRowColors(True)
        self.tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tracks.customContextMenuRequested.connect(self._context_menu)
        self.tracks.itemDoubleClicked.connect(self._play_track)
        self.tracks.setColumnWidth(0, 48)
        self.tracks.setColumnWidth(1, 390)
        self.tracks.setColumnWidth(2, 220)
        detail_layout.addWidget(self.tracks, 1)
        self.stack.addWidget(detail)

    def refresh(self) -> None:
        self.grid.clear()
        self._album_items.clear()
        self._album_rows.clear()
        for album in self.database.get_albums(self.compilations):
            item = QListWidgetItem()
            item.setSizeHint(QSize(168, 226))
            item.setData(Qt.ItemDataRole.UserRole, int(album["id"]))
            item.setData(Qt.ItemDataRole.UserRole + 1, album["artist_name"] or album["album_artist"])
            self.grid.addItem(item)
            self.grid.setItemWidget(item, self._card(album))
            self._album_items[int(album["id"])] = item
            self._album_rows[int(album["id"])] = album
        self._filter_collections(self.collection_search.text())

    def _filter_collections(self, text: str) -> None:
        query = text.strip().casefold()
        for index in range(self.grid.count()):
            item = self.grid.item(index)
            widget = self.grid.itemWidget(item)
            title = widget.findChild(QLabel, "albumCardTitle") if widget else None
            artist = widget.findChild(QLabel, "albumCardArtist") if widget else None
            searchable = " ".join(
                label.text() for label in (title, artist) if label is not None
            ).casefold()
            item.setHidden(bool(query) and query not in searchable)

    def _card(self, album: object) -> QWidget:
        card = QFrame()
        card.setObjectName("albumCard")
        card.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        box = QVBoxLayout(card)
        box.setContentsMargins(7, 7, 7, 7)
        box.setSpacing(4)
        cover = QLabel()
        cover.setObjectName("albumCardCover")
        cover.setFixedSize(142, 142)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setPixmap(self._scaled_cover(_album_pixmap(album, album["artist_name"] or album["album_artist"])))
        title = QLabel(album["title"])
        title.setObjectName("albumCardTitle")
        title.setFixedHeight(18)
        title.setToolTip(album["title"])
        artist = QLabel(album["artist_name"] or album["album_artist"])
        artist.setObjectName("albumCardArtist")
        artist.setFixedHeight(16)
        total = QLabel(
            f'{album["track_count"]} pistas · {_total_duration(album["total_duration"])}'
        )
        total.setObjectName("mutedLabel")
        total.setFixedHeight(15)
        box.addWidget(cover)
        box.addWidget(title)
        box.addWidget(artist)
        box.addWidget(total)
        return card

    def _album_context_menu(self, position: object) -> None:
        item = self.grid.itemAt(position)
        if item is None:
            return
        self.grid.setCurrentItem(item)
        album_id = int(item.data(Qt.ItemDataRole.UserRole))
        album = self._album_rows[album_id]
        menu = QMenu(self)
        online = menu.addAction("Buscar carátula en internet…")
        choose = menu.addAction("Buscar una carátula en el equipo…")
        preview = menu.addAction("Ver carátula en grande")
        selected = menu.exec(self.grid.viewport().mapToGlobal(position))
        widget = self.grid.itemWidget(item)
        cover = widget.findChild(QLabel, "albumCardCover") if widget else None
        if selected == preview:
            show_artwork(
                self,
                album["title"],
                cover.pixmap() if cover and cover.pixmap() else QPixmap(),
            )
        elif selected in (online, choose):
            artist = album["artist_name"] or album["album_artist"]
            online_data = (
                choose_online_artwork(
                    self, album["title"], kind="album", artist=artist
                )
                if selected == online
                else None
            )
            source = (
                choose_artwork(self, f'Carátula de {album["title"]}')
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
            self.update_album_cover(album_id, data)
            self.manual_cover_selected.emit(album_id, data)

    @staticmethod
    def _scaled_cover(pixmap: QPixmap) -> QPixmap:
        return pixmap.scaled(142, 142, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

    def show_root(self) -> None:
        self.stack.setCurrentIndex(0)
        self.collection_search.clear()
        self.track_search.clear()
        self.grid.clearSelection()
        self.grid.verticalScrollBar().setValue(0)

    def _open_album(self, item: QListWidgetItem) -> None:
        album_id = int(item.data(Qt.ItemDataRole.UserRole))
        self._current_album_id = album_id
        album = next(row for row in self.database.get_albums(self.compilations) if row["id"] == album_id)
        self.album_heading.setText(album["title"])
        self.artist_heading.setText(album["artist_name"] or album["album_artist"])
        self.track_search.clear()
        self._fill_tracks(album_id)
        self.stack.setCurrentIndex(1)

    def _fill_tracks(self, album_id: int) -> None:
        self.tracks.clear()
        rows = self.database.get_tracks_for_album(album_id)
        for index, row in enumerate(rows):
            item = _track_item(row)
            context = {"artist_id": row["artist_id"], "album_id": album_id, "is_compilation": bool(row["is_compilation"]), "file_path": row["file_path"]}
            item.setData(0, Qt.ItemDataRole.UserRole, _play_payload(rows, index, context))
            item.setData(0, Qt.ItemDataRole.UserRole + 1, _queue([row])[0])
            self.tracks.addTopLevelItem(item)
        if self._playing_file:
            mark_playing_track(self.tracks, self._playing_file)

    def _filter_tracks(self, text: str) -> None:
        query = text.strip().casefold()
        for index in range(self.tracks.topLevelItemCount()):
            item = self.tracks.topLevelItem(index)
            searchable = " ".join(item.text(column) for column in (1, 2)).casefold()
            item.setHidden(bool(query) and query not in searchable)

    def _play_album(self) -> None:
        rows = self.database.get_tracks_for_album(self._current_album_id)
        if rows:
            row = rows[0]
            self.play_requested.emit(_play_payload(rows, context={"artist_id": row["artist_id"], "album_id": self._current_album_id, "is_compilation": bool(row["is_compilation"])}))

    def _play_track(self, item: QTreeWidgetItem, _column: int) -> None:
        self.play_requested.emit(item.data(0, Qt.ItemDataRole.UserRole))

    def _context_menu(self, position: object) -> None:
        item = self.tracks.itemAt(position)
        if item is None:
            return
        self.tracks.setCurrentItem(item)
        menu = QMenu(self)
        action = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.tracks.viewport().mapToGlobal(position))
        if selected == action:
            self.enqueue_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))
        elif selected == playlist:
            self.playlist_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))

    def update_album_cover(self, album_id: int, data: bytes) -> None:
        item = self._album_items.get(album_id)
        if item is None:
            return
        pixmap = QPixmap()
        album = self._album_rows.get(album_id)
        artist = (album["artist_name"] or album["album_artist"]) if album else ""
        primary = _primary_artist_pixmap(artist)
        if not primary.isNull():
            pixmap = primary
        else:
            pixmap.loadFromData(data)
        if not pixmap.isNull():
            widget = self.grid.itemWidget(item)
            cover = widget.findChild(QLabel, "albumCardCover") if widget else None
            if cover:
                cover.setPixmap(self._scaled_cover(pixmap))

    def update_artist_image(self, artist: str, data: bytes) -> None:
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        for album_id, album in self._album_rows.items():
            album_artist = album["artist_name"] or album["album_artist"]
            if album_artist.casefold() != artist.casefold():
                continue
            item = self._album_items.get(album_id)
            widget = self.grid.itemWidget(item) if item else None
            cover = widget.findChild(QLabel, "albumCardCover") if widget else None
            if cover:
                cover.setPixmap(self._scaled_cover(pixmap))

    def locate(self, album_id: int | None, file_path: str) -> bool:
        if album_id is None or album_id not in self._album_items:
            return False
        item = self._album_items[album_id]
        self.grid.setCurrentItem(item)
        self._open_album(item)
        for index in range(self.tracks.topLevelItemCount()):
            track = self.tracks.topLevelItem(index)
            payload = track.data(0, Qt.ItemDataRole.UserRole)
            if payload.get("context", {}).get("file_path") == file_path:
                self.tracks.setCurrentItem(track)
                self.tracks.scrollToItem(track)
                break
        return True

    def mark_playing(self, file_path: str) -> bool:
        return mark_playing_track(self.tracks, file_path)

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.tracks, file_path)
