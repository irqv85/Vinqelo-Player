"""Panel principal con estadísticas e historial de escucha."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from library.artist_art import collage_cache_files
from library.cover_art import cover_cache_path
from library.manual_art import manual_artist_image_path, read_image
from ui.icons import navigation_icon
from ui.i18n import translate_text
from ui.pages.collection_pages import (
    _collage_pixmap,
    _default_pixmap,
    _play_payload,
    connect_track_click,
    mark_playing_track,
)
from ui.widgets.stat_card import StatCard


class LibraryPage(QWidget):
    add_folder_requested = Signal()
    open_file_requested = Signal()
    play_requested = Signal(object)
    enqueue_requested = Signal(object)
    playlist_requested = Signal(object)
    artist_requested = Signal(object)
    update_library_requested = Signal()
    export_library_requested = Signal()

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._database = database
        self._playing_file = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(6)

        header = QHBoxLayout()
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        eyebrow = QLabel("COLECCIÓN LOCAL")
        eyebrow.setObjectName("pageEyebrow")
        title = QLabel("Biblioteca")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Tu música y actividad de reproducción en un solo lugar.")
        subtitle.setObjectName("pageSubtitle")
        text_box.addWidget(eyebrow)
        text_box.addWidget(title)
        text_box.addWidget(subtitle)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        open_button = QPushButton()
        self.open_button = open_button
        open_button.setObjectName("toolbarIcon")
        open_button.setIcon(navigation_icon("file", "#dce7f7"))
        open_button.setIconSize(QSize(16, 16))
        open_button.setToolTip("Abrir un archivo")
        open_button.setFixedSize(32, 32)
        open_button.clicked.connect(self.open_file_requested.emit)
        update_button = QPushButton()
        self.update_button = update_button
        update_button.setObjectName("toolbarIcon")
        update_button.setIcon(navigation_icon("refresh", "#dce7f7"))
        update_button.setIconSize(QSize(16, 16))
        update_button.setToolTip("Actualizar biblioteca")
        update_button.setFixedSize(32, 32)
        update_button.clicked.connect(self.update_library_requested.emit)
        export_button = QPushButton()
        self.export_button = export_button
        export_button.setObjectName("toolbarIcon")
        export_button.setIcon(navigation_icon("export", "#8fa7c7"))
        export_button.setIconSize(QSize(16, 16))
        export_button.setToolTip("Exportar biblioteca")
        export_button.setFixedSize(32, 32)
        export_button.clicked.connect(self.export_library_requested.emit)
        add_button = QPushButton()
        self.add_button = add_button
        add_button.setObjectName("toolbarIconPrimary")
        add_button.setIcon(navigation_icon("folder_add", "#ffffff"))
        add_button.setIconSize(QSize(16, 16))
        add_button.setToolTip("Agregar raíz de biblioteca")
        add_button.setFixedSize(32, 32)
        add_button.clicked.connect(self.add_folder_requested.emit)
        actions.addWidget(open_button)
        actions.addWidget(update_button)
        actions.addWidget(export_button)
        actions.addWidget(add_button)
        header.addLayout(text_box, 1)
        header.addLayout(actions)
        layout.addLayout(header)
        layout.addSpacing(14)

        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(9)
        self._stats = {
            "artists": StatCard("Artistas"),
            "albums": StatCard("Álbumes"),
            "compilations": StatCard("Compilaciones"),
            "tracks": StatCard("Pistas"),
            "duration": StatCard("Duración total"),
        }
        for column, card in enumerate(self._stats.values()):
            stats_layout.addWidget(card, 0, column)
        layout.addLayout(stats_layout)
        self._format_stats_layout = QGridLayout()
        self._format_stats_layout.setHorizontalSpacing(9)
        self._format_cards: list[StatCard] = []
        layout.addLayout(self._format_stats_layout)
        layout.addSpacing(12)

        dashboard = QHBoxLayout()
        dashboard.setSpacing(12)
        artists_panel = self._panel("ARTISTAS MÁS ESCUCHADOS")
        artist_layout = artists_panel.layout()
        self.top_artists = QListWidget()
        self.top_artists.setObjectName("listeningArtists")
        self.top_artists.setIconSize(QSize(58, 58))
        self.top_artists.setSpacing(4)
        self.top_artists.itemDoubleClicked.connect(self._open_top_artist)
        artist_layout.addWidget(self.top_artists, 1)
        dashboard.addWidget(artists_panel, 2)

        tracks_panel = self._panel("CANCIONES MÁS ESCUCHADAS")
        track_layout = tracks_panel.layout()
        self.top_tracks = QTreeWidget()
        self.top_tracks.setObjectName("listeningTracks")
        self.top_tracks.setHeaderLabels(["CANCIÓN", "ARTISTA", "TIEMPO ESCUCHADO"])
        self.top_tracks.setRootIsDecorated(False)
        self.top_tracks.setAlternatingRowColors(True)
        self.top_tracks.setIconSize(QSize(48, 48))
        self.top_tracks.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.top_tracks.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.top_tracks.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        connect_track_click(self.top_tracks, self._play_top_track)
        self.top_tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.top_tracks.customContextMenuRequested.connect(self._top_track_menu)
        track_layout.addWidget(self.top_tracks, 1)
        dashboard.addWidget(tracks_panel, 3)
        layout.addLayout(dashboard, 1)

        self._selection_label = QLabel("")
        self._selection_label.setObjectName("mutedLabel")
        layout.addWidget(self._selection_label)

    @staticmethod
    def _panel(title: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("libraryPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 12, 14, 14)
        panel_layout.setSpacing(9)
        label = QLabel(title)
        label.setObjectName("columnHeader")
        panel_layout.addWidget(label)
        return panel

    def refresh_stats(self) -> None:
        stats = self._database.get_library_stats()
        for key in ("artists", "albums", "compilations", "tracks"):
            self._stats[key].set_value(stats[key])
        summary = self._database.get_media_summary()
        self._stats["duration"].set_value(
            format_library_duration(float(summary["total_duration"] or 0))
        )
        self._refresh_format_cards(summary["formats"])
        self.refresh_dashboard()

    def apply_theme(self, theme: str) -> None:
        """Mantiene legibles los iconos sobre temas claros u oscuros."""
        foreground = "#2d4358" if theme == "musicmatch" else "#dce7f7"
        muted = "#4f6982" if theme == "musicmatch" else "#8fa7c7"
        self.open_button.setIcon(navigation_icon("file", foreground))
        self.update_button.setIcon(navigation_icon("refresh", foreground))
        self.export_button.setIcon(navigation_icon("export", muted))
        self.add_button.setIcon(navigation_icon("folder_add", "#ffffff"))

    def _refresh_format_cards(self, formats: object) -> None:
        while self._format_stats_layout.count():
            item = self._format_stats_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._format_cards.clear()
        rows = list(formats) if isinstance(formats, list) else []
        for column, row in enumerate(rows):
            bitrate = round(float(row["average_bitrate"] or 0))
            caption = (
                f'{row["file_format"]} · {bitrate} kbps '
                f'{translate_text("promedio")}'
                if bitrate > 0
                else str(row["file_format"])
            )
            card = StatCard(caption)
            card.setMinimumHeight(64)
            card.set_value(int(row["track_count"] or 0))
            self._format_stats_layout.addWidget(card, 0, column)
            self._format_cards.append(card)

    def refresh_dashboard(self) -> None:
        self.top_artists.clear()
        artists = self._database.get_top_artists()
        if not artists:
            item = QListWidgetItem("Aún no hay reproducciones. Tu actividad aparecerá aquí.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.top_artists.addItem(item)
        for position, artist in enumerate(artists, start=1):
            manual_data = read_image(manual_artist_image_path(artist["name"]))
            manual_pixmap = QPixmap()
            if manual_data:
                manual_pixmap.loadFromData(manual_data)
            paths = [] if not manual_pixmap.isNull() else list(collage_cache_files(artist["name"]))
            if artist["id"] is not None:
                for album in self._database.get_albums_for_artist(int(artist["id"])):
                    if album["title"] == "Pistas sueltas":
                        continue
                    paths.append(cover_cache_path(album["title"], artist["name"]))
                    if album["cover_path"]:
                        paths.append(Path(album["cover_path"]))
            elif artist["album_id"] is not None:
                album = self._database.get_album_by_id(int(artist["album_id"]))
                if album is not None:
                    paths.append(
                        cover_cache_path(album["title"], artist["name"])
                    )
                    if album["cover_path"]:
                        paths.append(Path(album["cover_path"]))
            covers = (
                [manual_pixmap]
                if not manual_pixmap.isNull()
                else [QPixmap(str(path)) for path in paths if path.is_file()][:4]
            )
            covers = [pixmap for pixmap in covers if not pixmap.isNull()]
            icon_pixmap = (
                _collage_pixmap(covers, 58)
                if covers
                else _collage_pixmap([_default_pixmap(58)], 58)
            )
            seconds = int(artist["listen_seconds"] or 0)
            item = QListWidgetItem(
                QIcon(icon_pixmap),
                f'{position}.  {artist["name"]}\n     {format_listening_time(seconds)} escuchados',
            )
            item.setSizeHint(QSize(0, 70))
            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "artist_id": (
                        int(artist["id"]) if artist["id"] is not None else None
                    ),
                    "album_id": (
                        int(artist["album_id"])
                        if artist["album_id"] is not None else None
                    ),
                    "is_compilation": bool(artist["is_compilation"]),
                },
            )
            item.setToolTip(f'Ir a {artist["name"]}')
            self.top_artists.addItem(item)

        self.top_tracks.clear()
        tracks = self._database.get_top_tracks()
        if not tracks:
            empty = QTreeWidgetItem(["Aún no hay canciones reproducidas.", "", ""])
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self.top_tracks.addTopLevelItem(empty)
        for position, row in enumerate(tracks, start=1):
            artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
            item = QTreeWidgetItem(
                [
                    f'{position}.  {row["title"]}',
                    artist,
                    format_listening_time(int(row["listen_seconds"] or 0)),
                ]
            )
            item.setIcon(0, QIcon(self._track_cover(row, artist)))
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                _play_payload(
                    tracks,
                    position - 1,
                    {
                        "artist_id": row["artist_id"],
                        "album_id": row["album_id"],
                        "is_compilation": bool(row["is_compilation"]),
                        "file_path": row["file_path"],
                    },
                ),
            )
            item.setData(
                0,
                Qt.ItemDataRole.UserRole + 1,
                {
                    "file_path": row["file_path"],
                    "artist": artist,
                    "album": row["album_title"],
                },
            )
            self.top_tracks.addTopLevelItem(item)
        if self._playing_file:
            mark_playing_track(
                self.top_tracks, self._playing_file, title_column=0
            )

    @staticmethod
    def _track_cover(row: object, artist: str) -> QPixmap:
        candidates = [
            cover_cache_path(row["album_title"], artist),
            Path(row["cover_path"]) if row["cover_path"] else None,
        ]
        for path in candidates:
            if path and path.is_file():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    return pixmap
        if row["album_title"] == "Pistas sueltas":
            covers = [
                QPixmap(str(path)) for path in collage_cache_files(artist)[:4]
            ]
            covers = [pixmap for pixmap in covers if not pixmap.isNull()]
            if covers:
                return _collage_pixmap(covers, 48)
        manual_data = read_image(manual_artist_image_path(artist))
        manual = QPixmap()
        if manual_data:
            manual.loadFromData(manual_data)
        if not manual.isNull():
            return manual
        return _default_pixmap(48)

    def _play_top_track(self, item: QTreeWidgetItem, _column: int) -> None:
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if payload:
            self.play_requested.emit(payload)

    def _open_top_artist(self, item: QListWidgetItem) -> None:
        destination = item.data(Qt.ItemDataRole.UserRole)
        if destination:
            self.artist_requested.emit(destination)

    def _top_track_menu(self, position: object) -> None:
        item = self.top_tracks.itemAt(position)
        if item is None or not item.data(0, Qt.ItemDataRole.UserRole + 1):
            return
        self.top_tracks.setCurrentItem(item)
        menu = QMenu(self)
        add = menu.addAction("Añadir a la cola")
        playlist = menu.addAction("Añadir a lista de reproducción…")
        selected = menu.exec(self.top_tracks.viewport().mapToGlobal(position))
        if selected == add:
            self.enqueue_requested.emit(
                item.data(0, Qt.ItemDataRole.UserRole + 1)
            )
        elif selected == playlist:
            self.playlist_requested.emit(item.data(0, Qt.ItemDataRole.UserRole + 1))

    def show_selected_folder(self, path: Path) -> None:
        self._selection_label.setText(f"Analizando biblioteca: {path}")

    def set_playing_file(self, file_path: str) -> None:
        self._playing_file = file_path
        mark_playing_track(self.top_tracks, file_path, title_column=0)


def format_listening_time(seconds: int) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, remaining_seconds = divmod(remainder, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    if minutes:
        return f"{minutes} min {remaining_seconds:02d} s"
    return f"{remaining_seconds} s"


def format_library_duration(seconds: float) -> str:
    total_hours = max(0.0, float(seconds or 0) / 3600)
    if total_hours < 24:
        return f"{total_hours:.1f} h"
    days = int(total_hours // 24)
    hours = round(total_hours - days * 24)
    return f"{days} d {hours} h"
