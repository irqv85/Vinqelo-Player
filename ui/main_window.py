"""Ventana principal de Vinqelo Player."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from PySide6.QtCore import (
    QEvent,
    QRectF,
    QSettings,
    QSize,
    QStandardPaths,
    Signal,
    QThread,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QCloseEvent,
    QIcon,
    QKeySequence,
    QMouseEvent,
    QPainterPath,
    QRegion,
    QResizeEvent,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollBar,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import ASSETS_DIR
from database.manager import DatabaseManager
from library.cover_art import CoverArtService
from library.scanner import (
    LibraryRootsSyncWorker,
    LibraryScanWorker,
)
from library.track_metadata import TrackDetails
from player.controller import PlayerController, PlayerUnavailableError
from player.windows_media_session import WindowsMediaSession
from ui.effects_dialog import EffectsDialog
from ui.about_dialog import AboutDialog
from ui.loading_banner import LoadingBanner
from ui.icons import navigation_icon, window_control_icon
from ui.i18n import translate_text
from ui.pages.album_page import AlbumGridPage
from ui.pages.collection_pages import ArtistsPage
from ui.pages.folders_page import FoldersPage
from ui.pages.library_page import LibraryPage
from ui.pages.playlists_page import PlaylistsPage
from ui.pages.queue_page import QueuePage
from ui.pages.search_page import SearchPage
from ui.pages.smart_playlists_page import SmartPlaylistsPage
from ui.settings_dialog import SettingsDialog
from ui.styles import build_stylesheet
from ui.widgets.player_bar import PlayerBar
from ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    RESIZE_MARGIN = 7
    media_action_requested = Signal(str)

    def __init__(
        self, database: DatabaseManager, *, confirm_initial_library: bool = True
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._database = database
        self._pages: dict[str, QWidget] = {}
        self._dirty_sections: set[str] = set()
        self._player_controller: PlayerController | None = None
        self._windows_media_session: WindowsMediaSession | None = None
        self._effects_dialog: EffectsDialog | None = None
        self._player_error_message = ""
        self._cover_art = CoverArtService(self)
        self._settings = QSettings("Vinqelo", "Vinqelo Player")
        self._mask_timer = QTimer(self)
        self._mask_timer.setSingleShot(True)
        self._mask_timer.setInterval(35)
        self._mask_timer.timeout.connect(self._apply_window_mask)
        self._resize_cursor = Qt.CursorShape.ArrowCursor
        self._scan_thread: QThread | None = None
        self._scan_worker: LibraryScanWorker | None = None
        self._sync_thread: QThread | None = None
        self._sync_worker: LibraryRootsSyncWorker | None = None
        self._pending_sync_roots: set[str] = set()
        self._sync_timer = QTimer(self)
        self._sync_timer.setSingleShot(True)
        self._sync_timer.setInterval(1400)
        self._sync_timer.timeout.connect(self._start_library_sync)
        self._playback_context: dict[str, object] = {}
        self._repeat_mode = "off"
        self._shuffle_mode = "off"
        self._listening_file = ""
        self._listened_seconds = 0
        self._persisted_listen_seconds = 0
        self._qualified_play_recorded = False
        self._media_keyboard_hook: object | None = None
        self._media_hook_callback: object | None = None
        self._media_hotkey_ids: dict[int, str] = {}
        self._media_shortcuts: list[QShortcut] = []
        self._last_media_action: dict[str, float] = {}
        self._listening_timer = QTimer(self)
        self._listening_timer.setInterval(1000)
        self._listening_timer.timeout.connect(self._count_listening_second)
        self._listening_timer.start()
        self.media_action_requested.connect(
            self._run_media_action,
            Qt.ConnectionType.QueuedConnection,
        )
        self._create_media_shortcuts()

        self.setWindowTitle("Vinqelo Player — Biblioteca")
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "icons" / "vinqelo-v.png")))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(900, 620)
        self.resize(1240, 790)
        saved_geometry = self._settings.value("window/geometry")
        if saved_geometry:
            self.restoreGeometry(saved_geometry)

        root = QFrame()
        root.setObjectName("windowFrame")
        self._window_frame = root
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName("contentArea")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.stack = QStackedWidget()

        self.library_page = LibraryPage(database)
        self._add_page("library", self.library_page)
        self.search_page = SearchPage(database)
        self.artists_page = ArtistsPage(database)
        self.albums_page = AlbumGridPage(database)
        self.compilations_page = AlbumGridPage(database, compilations=True)
        self.folders_page = FoldersPage(database)
        self.smart_playlists_page = SmartPlaylistsPage(database)
        self.playlists_page = PlaylistsPage(database)
        self.queue_page = QueuePage(database)
        self._add_page("search", self.search_page)
        self._add_page("artists", self.artists_page)
        self._add_page("albums", self.albums_page)
        self._add_page("compilations", self.compilations_page)
        self._add_page("folders", self.folders_page)
        self._add_page("smart_playlists", self.smart_playlists_page)
        self._add_page("playlists", self.playlists_page)
        self._add_page("queue", self.queue_page)
        self._dirty_sections.update(
            {
                "artists",
                "albums",
                "compilations",
                "folders",
                "smart_playlists",
                "playlists",
            }
        )

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.stack, 1)
        self.player_bar = PlayerBar()
        root_layout.addWidget(content, 1)
        root_layout.addWidget(self.player_bar)
        self.setCentralWidget(root)
        self._loading_banner = LoadingBanner(self)

        self._create_window_controls(root)

        self.sidebar.section_selected.connect(self.show_section)
        self.sidebar.about_requested.connect(self._show_about)
        self.library_page.add_folder_requested.connect(self.select_folder)
        self.library_page.update_library_requested.connect(self.update_library)
        self.library_page.open_file_requested.connect(self.open_audio_file)
        self.library_page.play_requested.connect(self._play_library_items)
        self.library_page.enqueue_requested.connect(self._enqueue_library_item)
        self.library_page.artist_requested.connect(self._open_artist_from_dashboard)
        self.search_page.play_requested.connect(self._play_library_items)
        self.search_page.enqueue_requested.connect(self._enqueue_library_item)
        for page in (
            self.artists_page,
            self.albums_page,
            self.compilations_page,
            self.folders_page,
            self.smart_playlists_page,
        ):
            page.play_requested.connect(self._play_library_items)
            page.enqueue_requested.connect(self._enqueue_library_item)
        for page in (
            self.library_page,
            self.search_page,
            self.artists_page,
            self.albums_page,
            self.compilations_page,
            self.folders_page,
            self.smart_playlists_page,
        ):
            playlist_signal = getattr(page, "playlist_requested", None)
            if playlist_signal is not None:
                playlist_signal.connect(self._add_item_to_playlist)
        self.playlists_page.play_requested.connect(self._play_library_items)
        self.playlists_page.enqueue_requested.connect(self._enqueue_library_item)
        self.folders_page.metadata_changed.connect(self._handle_library_metadata_change)
        for page in (self.artists_page, self.albums_page, self.compilations_page, self.folders_page):
            page.classification_changed.connect(self._handle_classification_changed)
        self.artists_page.album_cover_ready.connect(self._handle_library_album_cover)
        self.artists_page.album_cover_ready.connect(self.albums_page.update_album_cover)
        self.artists_page.album_cover_ready.connect(self.compilations_page.update_album_cover)
        self.albums_page.manual_cover_selected.connect(self.artists_page._set_album_cover)
        self.compilations_page.manual_cover_selected.connect(self.artists_page._set_album_cover)
        self.artists_page.artwork_changed.connect(self.library_page.refresh_dashboard)
        self.artists_page.primary_artist_changed.connect(
            self.albums_page.update_artist_image
        )
        self.artists_page.primary_artist_changed.connect(
            self.compilations_page.update_artist_image
        )
        self._cover_art.cover_ready.connect(self.player_bar.set_cover_data)
        self._cover_art.cover_ready.connect(self._handle_windows_cover)
        self._cover_art.cover_unavailable.connect(self.player_bar.set_cover_unavailable)
        self._cover_art.metadata_ready.connect(self._handle_online_metadata)
        self._initialize_player()
        self.show_section("library")
        QTimer.singleShot(0, self._restore_last_track_location)
        if confirm_initial_library:
            QTimer.singleShot(700, self._confirm_initial_library)

        root.installEventFilter(self)
        for child in root.findChildren(QWidget):
            child.installEventFilter(self)
            child.setMouseTracking(True)
        root.setMouseTracking(True)
        QTimer.singleShot(0, self._initialize_system_media)

    def _create_window_controls(self, parent: QWidget) -> None:
        self.window_controls = QWidget(parent)
        self.window_controls.setFixedSize(151, 34)
        controls_layout = QHBoxLayout(self.window_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(3)

        self.settings_button = QPushButton()
        self.minimize_button = QPushButton()
        self.maximize_button = QPushButton()
        self.close_button = QPushButton()
        for button in (
            self.settings_button,
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        ):
            button.setProperty("windowControl", True)
            button.setFixedSize(34, 30)
            button.setIconSize(QSize(18, 18))
            controls_layout.addWidget(button)
        self.close_button.setProperty("closeControl", True)
        self.settings_button.setIcon(navigation_icon("settings", "#dce8f8"))
        self.minimize_button.setIcon(window_control_icon("minimize"))
        self.maximize_button.setIcon(window_control_icon("maximize"))
        self.close_button.setIcon(window_control_icon("close"))

        self.settings_button.setToolTip("Configuración")
        self.minimize_button.setToolTip("Minimizar")
        self.maximize_button.setToolTip("Maximizar")
        self.close_button.setToolTip("Cerrar")
        self.settings_button.clicked.connect(self._show_settings)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(self.close)
        self.window_controls.raise_()

    def _initialize_player(self) -> None:
        try:
            controller = PlayerController(self)
        except PlayerUnavailableError as exc:
            self._player_error_message = str(exc)
            self._logger.error("Reproducción no disponible: %s", exc)
            self.player_bar.set_engine_available(False, "VLC no está disponible")
            self.sidebar.set_player_available(False)
            return

        self._player_controller = controller
        self._effects_dialog = EffectsDialog(controller, self)
        self.player_bar.set_engine_available(True)
        self.sidebar.set_player_available(True)
        controller.track_changed.connect(self.player_bar.set_track)
        controller.track_changed.connect(self._update_playback_context)
        controller.track_details_changed.connect(self._handle_track_details)
        controller.state_changed.connect(self.player_bar.set_playback_state)
        controller.state_changed.connect(self._handle_history_state)
        controller.state_changed.connect(self._handle_now_playing_visibility)
        controller.position_changed.connect(self.player_bar.set_timing)
        controller.queue_navigation_changed.connect(self.player_bar.set_queue_navigation)
        controller.queue_changed.connect(self.queue_page.update_queue)
        controller.error_occurred.connect(self._show_player_error)

        self.player_bar.previous_requested.connect(controller.previous)
        self.player_bar.play_pause_requested.connect(controller.play_pause)
        self.player_bar.stop_requested.connect(controller.stop)
        self.player_bar.next_requested.connect(controller.next)
        self.queue_page.play_index_requested.connect(controller.play_index)
        self.player_bar.seek_requested.connect(controller.seek_to)
        self.player_bar.effects_requested.connect(self._show_effects)
        self.player_bar.repeat_mode_requested.connect(self._change_repeat_mode)
        self.player_bar.shuffle_mode_requested.connect(self._change_shuffle_mode)
        self.player_bar.now_playing_requested.connect(self._locate_now_playing)
        saved_volume = self._settings.value("player/volume", 70, type=int)
        self.player_bar.volume.setValue(max(0, min(100, saved_volume)))
        self.player_bar.volume_changed.connect(controller.set_volume)
        self.player_bar.volume_changed.connect(self._save_volume)
        controller.set_volume(self.player_bar.volume.value())

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.settings_applied.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, values: object) -> None:
        if not isinstance(values, dict):
            return
        application = QApplication.instance()
        if application is not None:
            application.setStyleSheet(
                build_stylesheet(
                    str(values.get("theme", "vinqelo")),
                    int(values.get("font_size", 13)),
                )
            )
            translation_manager = getattr(
                application, "_vinqelo_translation_manager", None
            )
            if translation_manager is not None:
                translation_manager.set_language(str(values.get("language", "es")))
                self.player_bar.retranslate_dynamic()
                # Las listas inteligentes generan sus títulos, contadores y
                # estados vacíos después de construirse; se regeneran aquí con
                # el idioma recién elegido.
                self.smart_playlists_page.refresh()
                self.folders_page.refresh()

    def _handle_track_details(self, details: TrackDetails) -> None:
        self.player_bar.set_track_details(details)
        if self._windows_media_session is not None:
            self._windows_media_session.set_track_details(details)
        self._cover_art.request_cover(details)

    def _handle_online_metadata(self, file_path: str, details: TrackDetails) -> None:
        if str(details.file_path) == file_path:
            self.player_bar.set_track_details(details)
            if self._windows_media_session is not None:
                self._windows_media_session.set_track_details(details)

    def _handle_windows_cover(self, file_path: str, data: bytes, _source: str) -> None:
        if self._windows_media_session is not None:
            self._windows_media_session.set_artwork(file_path, data)

    def _handle_library_album_cover(self, album_id: int, data: bytes) -> None:
        if self._playback_context.get("album_id") != album_id:
            return
        file_path = str(self._playback_context.get("file_path", ""))
        if file_path:
            self.player_bar.set_cover_data(
                file_path, data, "Carátula oficial de la biblioteca"
            )
            if self._windows_media_session is not None:
                self._windows_media_session.set_artwork(file_path, data)

    def _add_page(self, key: str, page: QWidget) -> None:
        self._pages[key] = page
        self.stack.addWidget(page)

    def _open_artist_from_dashboard(self, artist_id: int) -> None:
        self._ensure_section_loaded("artists")
        self.stack.setCurrentWidget(self.artists_page)
        self.sidebar.select("artists", emit_signal=False)
        self.artists_page.open_artist(int(artist_id))
        self.setWindowTitle("Vinqelo Player — Artistas")

    def show_section(self, section: str) -> None:
        if section == "now_playing":
            self._locate_now_playing()
            return
        page = self._pages.get(section)
        if page is not None:
            self._ensure_section_loaded(section)
            show_root = getattr(page, "show_root", None)
            if callable(show_root):
                show_root()
            self.stack.setCurrentWidget(page)
            self.sidebar.select(section, emit_signal=False)
            section_titles = {
                "library": "Biblioteca",
                "search": "Buscar",
                "artists": "Artistas",
                "albums": "Álbumes",
                "compilations": "Compilaciones",
                "folders": "Carpetas",
                "smart_playlists": "Smart Playlist",
                "playlists": "Listas de reproducción",
                "queue": "Cola de reproducción",
            }
            self.setWindowTitle(f"Vinqelo Player — {section_titles.get(section, 'Biblioteca')}")
            if section == "search":
                self.search_page.focus_search()
            elif section == "library":
                # Actualiza estadísticas y actividad una sola vez al entrar.
                # LibraryPage ya no repite esta consulta durante su construcción.
                self.library_page.refresh_stats()

    def update_library(self) -> None:
        if self._scan_thread is not None or self._sync_thread is not None:
            QMessageBox.information(
                self,
                "Actualización en curso",
                "La biblioteca ya se está actualizando.",
            )
            return
        registered = [Path(row["folder_path"]) for row in self._database.get_roots()]
        available = [path.resolve() for path in registered if path.is_dir()]
        unavailable = [path for path in registered if not path.is_dir()]
        for path in unavailable:
            self._logger.warning("Raíz de biblioteca no disponible: %s", path)
        if not registered:
            QMessageBox.information(
                self,
                "Biblioteca vacía",
                "Primero agrega una carpeta raíz a la biblioteca.",
            )
            return
        if not available:
            QMessageBox.warning(
                self,
                "Biblioteca no disponible",
                "No se encontró ninguna de las carpetas registradas.",
            )
            return
        self._pending_sync_roots.update(str(path) for path in available)
        self._start_library_sync()

    def _confirm_initial_library(self) -> None:
        """Confirma la carpeta Música una sola vez en una instalación nueva."""
        if self._database.get_roots():
            self._settings.setValue("library/initial_prompt_completed", True)
            return
        if self._settings.value(
            "library/initial_prompt_completed", False, type=bool
        ):
            return

        suggested_text = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.MusicLocation
        )
        suggested = Path(suggested_text) if suggested_text else Path.home() / "Music"
        dialog = QMessageBox(self)
        dialog.setObjectName("initialLibraryDialog")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle(translate_text("Configurar biblioteca de música"))
        dialog.setText(
            translate_text(
                "Windows indicó esta carpeta para tu música:\n\n"
                "{path}\n\n¿Quieres usarla como biblioteca principal?"
            ).format(path=suggested)
        )
        use_button = dialog.addButton(
            translate_text("Usar esta carpeta"), QMessageBox.ButtonRole.AcceptRole
        )
        choose_button = dialog.addButton(
            translate_text("Elegir otra carpeta"), QMessageBox.ButtonRole.ActionRole
        )
        later_button = dialog.addButton(
            translate_text("Configurar después"), QMessageBox.ButtonRole.RejectRole
        )
        for button in (use_button, choose_button, later_button):
            button.setObjectName("initialLibraryButton")
            button.setMinimumWidth(0)
        if not suggested.is_dir():
            use_button.setEnabled(False)
        dialog.exec()
        self._settings.setValue("library/initial_prompt_completed", True)
        clicked = dialog.clickedButton()
        if clicked is use_button:
            self._start_folder_import(suggested)
        elif clicked is choose_button:
            self.select_folder()
        elif clicked is later_button:
            return

    def select_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Agregar carpeta a la biblioteca",
            str(Path.home() / "Music"),
        )
        if not selected:
            return

        self._start_folder_import(Path(selected))

    def _start_folder_import(self, folder_path: Path) -> None:
        if not folder_path.exists() or not folder_path.is_dir():
            self._logger.warning("Se intentó seleccionar una carpeta inválida: %s", folder_path)
            QMessageBox.warning(self, "Carpeta no valida", "La carpeta seleccionada ya no existe.")
            return

        if self._scan_thread is not None:
            QMessageBox.information(self, "Importación en curso", "Ya se está analizando una carpeta.")
            return

        self._loading_banner.start(
            [
                "Validando cambios en la biblioteca…",
                "Actualizando la colección…",
                "Organizando los cambios detectados…",
            ]
        )

        self._scan_thread = QThread(self)
        self._scan_worker = LibraryScanWorker(folder_path)
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.finished.connect(self._finish_library_import)
        self._scan_worker.failed.connect(self._fail_library_import)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.failed.connect(self._scan_worker.deleteLater)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.failed.connect(self._scan_thread.quit)
        self._scan_thread.finished.connect(self._cleanup_scan)
        self._scan_thread.start()
        self.library_page.show_selected_folder(folder_path)
        self._logger.info("Analizando biblioteca: %s", folder_path)

    def _finish_library_import(self, scan: object) -> None:
        registered_roots = {
            str(Path(row["folder_path"]).resolve())
            for row in self._database.get_roots()
        }
        existing_root = str(Path(scan.root_path).resolve()) in registered_roots
        if not scan.artists and not existing_root:
            self._loading_banner.stop()
            QMessageBox.warning(
                self,
                "No se encontraron álbumes",
                "La carpeta debe tener esta estructura:\n\n"
                "Biblioteca / Artista / Álbum / Pista.mp3\n\n"
                "Los nombres de Artista y Álbum se toman únicamente de esas carpetas.",
            )
            return
        try:
            counts = self._database.synchronize_library_scan(scan)
            prepared = self.artists_page.prepare_artist_thumbnails(force=True)
            self.artists_page.queue_artwork_updates()
            self._logger.info("Miniaturas de artistas preparadas: %d", prepared)
            self._apply_sync_to_player(counts)
            self._refresh_library_pages()
            stats = self._database.get_library_stats()
            warning = f"\n\n{len(scan.warnings)} archivo(s) no pudieron leerse." if scan.warnings else ""
            self._loading_banner.stop()
            QMessageBox.information(
                self,
                "Biblioteca agregada",
                f"Artistas: {len(self._database.get_artists())}\n"
                f"Álbumes: {stats['albums']}\nCompilaciones: {stats['compilations']}\n"
                f"Pistas: {stats['tracks']}{warning}\n\n"
                "Haz doble clic en una carpeta, artista, álbum o pista para reproducir.",
            )
        except Exception as exc:
            self._loading_banner.stop()
            self._logger.exception("No se pudo guardar la biblioteca")
            QMessageBox.critical(self, "No se pudo importar", str(exc))

    def _fail_library_import(self, message: str) -> None:
        self._loading_banner.stop()
        self._logger.error("Falló el escaneo de biblioteca: %s", message)
        QMessageBox.warning(self, "No se pudo analizar la carpeta", message)

    def _cleanup_scan(self) -> None:
        self._loading_banner.stop()
        if self._scan_thread is not None:
            self._scan_thread.deleteLater()
        self._scan_worker = None
        self._scan_thread = None
        if self._pending_sync_roots:
            self._sync_timer.start()

    def _start_library_sync(self) -> None:
        if self._sync_thread is not None or self._scan_thread is not None:
            self._sync_timer.start(1800)
            return
        roots = [
            Path(path) for path in sorted(self._pending_sync_roots)
            if Path(path).is_dir()
        ]
        self._pending_sync_roots.clear()
        if not roots:
            return
        self._sync_thread = QThread(self)
        self._sync_worker = LibraryRootsSyncWorker(roots)
        self._sync_worker.moveToThread(self._sync_thread)
        self._sync_thread.started.connect(self._sync_worker.run)
        self._sync_worker.finished.connect(self._finish_library_sync)
        self._sync_worker.finished.connect(self._sync_worker.deleteLater)
        self._sync_worker.finished.connect(self._sync_thread.quit)
        self._sync_thread.finished.connect(self._cleanup_library_sync)
        self._loading_banner.start(
            [
                "Validando cambios en la biblioteca…",
                "Actualizando la colección…",
                "Organizando los cambios detectados…",
            ]
        )
        self._sync_thread.start()
        self._logger.info("Sincronizando %d raíz(es) de biblioteca", len(roots))

    def _finish_library_sync(self, scans: object, errors: object) -> None:
        moved: dict[str, str] = {}
        removed: list[str] = []
        try:
            for scan in scans if isinstance(scans, list) else []:
                result = self._database.synchronize_library_scan(scan)
                moved.update(result.get("moved_tracks", {}))
                removed.extend(result.get("removed_tracks", []))
            prepared = self.artists_page.prepare_artist_thumbnails(force=True)
            self.artists_page.queue_artwork_updates()
            self._logger.info("Miniaturas de artistas preparadas: %d", prepared)
            if scans:
                self._apply_sync_to_player(
                    {"moved_tracks": moved, "removed_tracks": removed}
                )
                self._refresh_library_pages()
            for error in errors if isinstance(errors, list) else []:
                self._logger.warning("Sincronización omitida: %s", error)
            self._logger.info(
                "Biblioteca sincronizada: %d movida(s), %d eliminada(s)",
                len(moved),
                len(removed),
            )
        except Exception:
            self._logger.exception("No se pudo sincronizar la biblioteca")

    def _apply_sync_to_player(self, result: object) -> None:
        if self._player_controller is None or not isinstance(result, dict):
            return
        moved = result.get("moved_tracks", {})
        removed = result.get("removed_tracks", [])
        if isinstance(moved, dict):
            if self._listening_file in moved:
                self._listening_file = str(moved[self._listening_file])
                self._playback_context["file_path"] = self._listening_file
            self._player_controller.replace_queue_paths(moved, removed)

    def _cleanup_library_sync(self) -> None:
        self._loading_banner.stop()
        if self._sync_thread is not None:
            self._sync_thread.deleteLater()
        self._sync_worker = None
        self._sync_thread = None
        if self._pending_sync_roots:
            self._sync_timer.start()

    def _refresh_library_pages(self) -> None:
        self.library_page.refresh_stats()
        self._dirty_sections.update(
            {
                "artists",
                "albums",
                "compilations",
                "folders",
                "smart_playlists",
                "playlists",
            }
        )
        current = next(
            (
                key for key, page in self._pages.items()
                if page is self.stack.currentWidget()
            ),
            "",
        )
        self._ensure_section_loaded(current)

    def _ensure_section_loaded(self, section: str) -> None:
        if section not in self._dirty_sections:
            return
        page = self._pages.get(section)
        refresh = getattr(page, "refresh", None)
        if callable(refresh):
            self._loading_banner.start(
                [
                    "Preparando la colección…",
                    "Organizando la información…",
                    "Casi listo…",
                ]
            )
            QApplication.processEvents()
            try:
                refresh()
            finally:
                self._loading_banner.stop()
        self._dirty_sections.discard(section)

    def _show_effects(self) -> None:
        if self._effects_dialog is None:
            return
        self._effects_dialog.show()
        self._effects_dialog.raise_()
        self._effects_dialog.activateWindow()

    def _handle_library_metadata_change(self, renamed: object) -> None:
        self._refresh_library_pages()
        if self._player_controller is not None:
            if isinstance(renamed, dict) and self._listening_file in renamed:
                self._listening_file = str(renamed[self._listening_file])
                self._playback_context["file_path"] = self._listening_file
            self._player_controller.replace_queue_paths(renamed)

    def _handle_classification_changed(self) -> None:
        """Actualiza las vistas afectadas sin volver a escanear los archivos."""
        self.library_page.refresh_dashboard()
        self._dirty_sections.update({"artists", "albums", "compilations", "folders"})
        current = next(
            (key for key, page in self._pages.items() if page is self.stack.currentWidget()),
            "",
        )
        self._ensure_section_loaded(current)

    def _add_item_to_playlist(self, item: object) -> None:
        if not isinstance(item, dict):
            return
        playlists = self._database.get_playlists()
        labels = [str(row["name"]) for row in playlists]
        labels.append("+ Crear nueva lista…")
        selected, accepted = QInputDialog.getItem(
            self, "Añadir a lista", "Lista de reproducción:", labels, 0, False
        )
        if not accepted:
            return
        if selected == "+ Crear nueva lista…":
            playlist_id = self.playlists_page.create_playlist()
            if playlist_id is None:
                return
        else:
            playlist_id = next(
                int(row["id"]) for row in playlists if row["name"] == selected
            )
        try:
            added = self._database.add_track_to_playlist(
                playlist_id, str(item.get("file_path", ""))
            )
            self.playlists_page.refresh(select_id=playlist_id)
            if not added:
                QMessageBox.information(
                    self, "Lista de reproducción", "La pista ya estaba en esa lista."
                )
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo añadir", str(exc))

    def _play_library_items(self, payload: object) -> None:
        if self._player_controller is None:
            return
        if isinstance(payload, dict):
            items = payload.get("items", [])
            start_index = int(payload.get("start_index", 0))
            self._playback_context = dict(payload.get("context", {}))
        else:
            items = payload
            start_index = 0
            self._playback_context = {}
        if not isinstance(items, list) or not items:
            return
        paths = [Path(item["file_path"]).resolve() for item in items]
        metadata = {
            str(path): (str(item["artist"]), str(item["album"]))
            for path, item in zip(paths, items)
        }
        self._playback_context["file_path"] = str(paths[start_index])
        self.sidebar.set_now_playing_available(True)
        self._player_controller.set_queue(
            paths,
            start_index=start_index,
            folder_metadata=metadata,
        )

    def _change_repeat_mode(self, mode: str) -> None:
        controller = self._player_controller
        if controller is None:
            return
        self._repeat_mode = mode if mode in {"off", "one", "queue"} else "off"
        controller.set_repeat_mode(
            "one" if self._repeat_mode == "one"
            else "all" if self._repeat_mode == "queue"
            else "off"
        )

    def _change_shuffle_mode(self, mode: str) -> None:
        controller = self._player_controller
        if controller is None:
            return
        self._shuffle_mode = mode if mode in {"off", "queue"} else "off"
        controller.set_shuffle(self._shuffle_mode == "queue")

    def _enqueue_library_item(self, item: object) -> None:
        if self._player_controller is None or not isinstance(item, dict):
            return
        path = Path(str(item.get("file_path", ""))).resolve()
        metadata = {
            str(path): (str(item.get("artist", "")), str(item.get("album", "")))
        }
        added = self._player_controller.enqueue_files([path], folder_metadata=metadata)
        if added:
            self._logger.info("Añadida a la cola: %s", path)

    def _update_playback_context(self, _title: str, _artist: str, file_path: str) -> None:
        self._flush_listening_time()
        self._listening_file = file_path
        self._listened_seconds = 0
        self._persisted_listen_seconds = 0
        self._qualified_play_recorded = False
        row = self._database.get_track_context(file_path)
        if row is None:
            self._playback_context = {"file_path": file_path}
            self.sidebar.set_now_playing_available(True)
            return
        self._playback_context = {
            "file_path": file_path,
            "album_id": int(row["album_id"]),
            "artist_id": int(row["artist_id"]),
            "is_compilation": bool(row["is_compilation"]),
        }
        self._settings.setValue("library/last_track", file_path)
        self.sidebar.set_now_playing_available(True)
        QTimer.singleShot(0, self._highlight_track_in_current_page)

    def _count_listening_second(self) -> None:
        controller = self._player_controller
        if (
            controller is None
            or controller.state.value != "playing"
            or controller.current_file is None
            or str(controller.current_file) != self._listening_file
        ):
            return
        self._listened_seconds += 1
        if self._listened_seconds < 30:
            return
        if not self._qualified_play_recorded:
            if self._database.get_track_context(self._listening_file) is None:
                return
            self._database.record_qualified_listen(
                self._listening_file, self._listened_seconds
            )
            self._persisted_listen_seconds = self._listened_seconds
            self._qualified_play_recorded = True
            self.library_page.refresh_dashboard()
        elif self._listened_seconds - self._persisted_listen_seconds >= 5:
            self._flush_listening_time()

    def _flush_listening_time(self) -> None:
        if not self._qualified_play_recorded or not self._listening_file:
            return
        pending = self._listened_seconds - self._persisted_listen_seconds
        if pending <= 0:
            return
        self._database.add_listen_time(self._listening_file, pending)
        self._persisted_listen_seconds = self._listened_seconds

    def _handle_history_state(self, state: str) -> None:
        if state != "playing":
            self._flush_listening_time()

    def _handle_now_playing_visibility(self, state: str) -> None:
        active = state in {"playing", "paused"}
        self.sidebar.set_now_playing_available(active)
        if not active and self.sidebar.is_selected("now_playing"):
            if self._playback_context.get("is_compilation"):
                self.sidebar.select("compilations", emit_signal=False)
            else:
                self.sidebar.select("artists", emit_signal=False)

    def _restore_last_track_location(self) -> None:
        """Restaura ubicación y carga la última pista sin reproducirla."""
        file_path = str(self._settings.value("library/last_track", "") or "")
        if not file_path:
            return
        row = self._database.get_track_context(file_path)
        if row is None:
            self._settings.remove("library/last_track")
            return
        album_id = int(row["album_id"])
        if bool(row["is_compilation"]):
            self._ensure_section_loaded("compilations")
            self.stack.setCurrentWidget(self.compilations_page)
            self.compilations_page.locate(album_id, file_path)
            self.sidebar.select("compilations", emit_signal=False)
            self.setWindowTitle("Vinqelo Player — Compilaciones")
        else:
            artist_id = int(row["artist_id"])
            self._ensure_section_loaded("artists")
            self.stack.setCurrentWidget(self.artists_page)
            self.artists_page.locate(artist_id, album_id, file_path)
            self.sidebar.select("artists", emit_signal=False)
            self.setWindowTitle("Vinqelo Player — Artistas")
        self._load_last_track_stopped(album_id, file_path)
        self.sidebar.set_now_playing_available(False)

    def _load_last_track_stopped(self, album_id: int, file_path: str) -> None:
        controller = self._player_controller
        if controller is None:
            return
        rows = [
            row for row in self._database.get_tracks_for_album(album_id)
            if Path(str(row["file_path"])).is_file()
        ]
        start_index = next(
            (
                index for index, row in enumerate(rows)
                if str(row["file_path"]) == file_path
            ),
            -1,
        )
        if start_index < 0:
            return
        paths = [Path(str(row["file_path"])).resolve() for row in rows]
        metadata = {
            str(path): (
                str(
                    (row["track_artist"] if row["is_compilation"] else row["artist_name"])
                    or ""
                ),
                str(row["album_title"]),
            )
            for path, row in zip(paths, rows)
        }
        controller.set_queue(
            paths,
            start_index=start_index,
            autoplay=False,
            folder_metadata=metadata,
        )

    def _highlight_track_in_current_page(self) -> None:
        file_path = str(self._playback_context.get("file_path", ""))
        if not file_path:
            return
        for page in (
            self.library_page,
            self.search_page,
            self.artists_page,
            self.albums_page,
            self.compilations_page,
            self.folders_page,
            self.smart_playlists_page,
            self.playlists_page,
        ):
            page.set_playing_file(file_path)

    def _locate_now_playing(self) -> None:
        if not self._playback_context:
            return
        album_id = self._playback_context.get("album_id")
        file_path = str(self._playback_context.get("file_path", ""))
        if self._playback_context.get("is_compilation"):
            self._ensure_section_loaded("compilations")
            self.stack.setCurrentWidget(self.compilations_page)
            self.compilations_page.locate(
                int(album_id) if album_id is not None else None, file_path
            )
        else:
            artist_id = self._playback_context.get("artist_id")
            if artist_id is None:
                return
            self._ensure_section_loaded("artists")
            self.stack.setCurrentWidget(self.artists_page)
            self.artists_page.locate(
                int(artist_id),
                int(album_id) if album_id is not None else None,
                file_path,
            )
        self.sidebar.select("now_playing", emit_signal=False)
        self.setWindowTitle("Vinqelo Player — Reproducción en curso")

    def _save_volume(self, value: int) -> None:
        self._settings.setValue("player/volume", int(value))

    def open_audio_file(self) -> None:
        if self._player_controller is None:
            QMessageBox.warning(
                self,
                "Reproducción no disponible",
                self._player_error_message
                or "No se encontró una instalación funcional de VLC Media Player.",
            )
            return

        music_folder = Path.home() / "Music"
        initial_folder = music_folder if music_folder.is_dir() else Path.home()
        selected, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo de audio",
            str(initial_folder),
            "Archivos de audio (*.mp3 *.flac *.wav *.ogg *.m4a *.aac);;Todos los archivos (*)",
        )
        if not selected:
            return

        self._logger.info("Abriendo archivo de audio: %s", selected)
        self.open_audio_paths([Path(selected)])

    def open_audio_paths(self, file_paths: list[Path]) -> None:
        """Abre archivos recibidos desde Windows o desde el selector interno."""
        if self._player_controller is None:
            return
        from library.audio_formats import is_supported_audio

        paths = [
            path.expanduser().resolve()
            for path in file_paths
            if is_supported_audio(path.expanduser())
        ]
        if not paths:
            return
        self._logger.info("Abriendo %d archivo(s) desde Windows", len(paths))
        self._playback_context = {}
        self.sidebar.set_now_playing_available(False)
        self._player_controller.set_queue(paths, start_index=0, autoplay=True)

    def _show_player_error(self, message: str) -> None:
        self._logger.error("Error de reproducción: %s", message)
        QMessageBox.warning(self, "No se pudo reproducir", message)

    def _show_about(self) -> None:
        AboutDialog(self).exec()

    def _toggle_maximized(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setIcon(window_control_icon("maximize"))
        else:
            self.showMaximized()
            self.maximize_button.setIcon(window_control_icon("restore"))

    def _initialize_system_media(self) -> None:
        """Prefiere la sesión multimedia oficial de Windows sobre hotkeys globales."""
        controller = self._player_controller
        if controller is None:
            return
        session = WindowsMediaSession(int(self.winId()), self)
        if not session.is_available:
            session.deleteLater()
            self._logger.info("Se usará el respaldo de teclas multimedia clásicas")
            self._register_media_hotkeys()
            return

        self._windows_media_session = session
        for shortcut in self._media_shortcuts:
            shortcut.setEnabled(False)
        session.action_requested.connect(
            self._queue_media_action,
            Qt.ConnectionType.QueuedConnection,
        )
        controller.state_changed.connect(session.set_playback_state)
        controller.position_changed.connect(session.update_timeline)
        controller.queue_navigation_changed.connect(session.set_navigation)

    def _register_media_hotkeys(self) -> None:
        """Escucha globalmente solo las teclas multimedia dedicadas en Windows."""
        if sys.platform != "win32" or self._player_controller is None:
            return
        try:
            import ctypes
            import ctypes.wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            class KeyboardData(ctypes.Structure):
                _fields_ = [
                    ("vkCode", ctypes.wintypes.DWORD),
                    ("scanCode", ctypes.wintypes.DWORD),
                    ("flags", ctypes.wintypes.DWORD),
                    ("time", ctypes.wintypes.DWORD),
                    ("extraInfo", ctypes.c_size_t),
                ]

            result_type = ctypes.c_ssize_t
            hook_proc_type = ctypes.WINFUNCTYPE(
                result_type,
                ctypes.c_int,
                ctypes.wintypes.WPARAM,
                ctypes.wintypes.LPARAM,
            )
            user32.SetWindowsHookExW.argtypes = [
                ctypes.c_int,
                hook_proc_type,
                ctypes.wintypes.HINSTANCE,
                ctypes.wintypes.DWORD,
            ]
            user32.CallNextHookEx.restype = result_type
            user32.CallNextHookEx.argtypes = [
                ctypes.wintypes.HHOOK,
                ctypes.c_int,
                ctypes.wintypes.WPARAM,
                ctypes.wintypes.LPARAM,
            ]
            user32.SetWindowsHookExW.restype = ctypes.wintypes.HHOOK
            kernel32.GetModuleHandleW.argtypes = [ctypes.wintypes.LPCWSTR]
            kernel32.GetModuleHandleW.restype = ctypes.wintypes.HMODULE
            media_keys = {
                0xB1: "previous",    # VK_MEDIA_PREV_TRACK
                0xB3: "play_pause",  # VK_MEDIA_PLAY_PAUSE
                0xB0: "next",        # VK_MEDIA_NEXT_TRACK
                0xB2: "stop",        # VK_MEDIA_STOP
            }

            def media_key_hook(code: int, message: int, data_pointer: int) -> int:
                if code >= 0 and int(message) in (0x0100, 0x0104):  # KEYDOWN / SYSKEYDOWN
                    keyboard = ctypes.cast(
                        data_pointer, ctypes.POINTER(KeyboardData)
                    ).contents
                    action = media_keys.get(int(keyboard.vkCode))
                    if action:
                        self._queue_media_action(action)
                return user32.CallNextHookEx(
                    self._media_keyboard_hook, code, message, data_pointer
                )

            self._media_hook_callback = hook_proc_type(media_key_hook)
            module = kernel32.GetModuleHandleW(None)
            self._media_keyboard_hook = user32.SetWindowsHookExW(
                13,  # WH_KEYBOARD_LL
                self._media_hook_callback,
                module,
                0,
            )
            if not self._media_keyboard_hook:
                self._media_hook_callback = None
                raise ctypes.WinError()

            window_handle = int(self.winId())
            global_keys = {
                0xA101: (0xB1, "previous"),
                0xA102: (0xB3, "play_pause"),
                0xA103: (0xB0, "next"),
                0xA104: (0xB2, "stop"),
            }
            for hotkey_id, (virtual_key, action) in global_keys.items():
                if user32.RegisterHotKey(window_handle, hotkey_id, 0x4000, virtual_key):
                    self._media_hotkey_ids[hotkey_id] = action
            self._logger.info(
                "Teclas multimedia activadas: hook global y %s hotkeys",
                len(self._media_hotkey_ids),
            )
        except Exception:
            self._logger.exception("No se pudieron registrar las teclas multimedia")

    def _unregister_media_hotkeys(self) -> None:
        if sys.platform != "win32":
            return
        try:
            import ctypes

            user32 = ctypes.windll.user32
            window_handle = int(self.winId())
            for hotkey_id in tuple(self._media_hotkey_ids):
                user32.UnregisterHotKey(window_handle, hotkey_id)
            if self._media_keyboard_hook:
                user32.UnhookWindowsHookEx(self._media_keyboard_hook)
        finally:
            self._media_hotkey_ids.clear()
            self._media_keyboard_hook = None
            self._media_hook_callback = None

    def _create_media_shortcuts(self) -> None:
        """Respaldo local: solamente teclas multimedia, nunca letras o Ctrl."""
        keys = {
            Qt.Key.Key_MediaPrevious: "previous",
            Qt.Key.Key_MediaTogglePlayPause: "play_pause",
            Qt.Key.Key_MediaNext: "next",
            Qt.Key.Key_MediaStop: "stop",
        }
        for key, action in keys.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(
                lambda selected=action: self._queue_media_action(selected)
            )
            self._media_shortcuts.append(shortcut)

    def _queue_media_action(self, action: str) -> None:
        """Une las rutas de Windows y evita dobles acciones por una pulsación."""
        now = time.monotonic()
        if now - self._last_media_action.get(action, 0.0) < 0.18:
            return
        self._last_media_action[action] = now
        self.media_action_requested.emit(action)

    def _run_media_action(self, action: str) -> None:
        controller = self._player_controller
        if controller is None:
            return
        actions = {
            "previous": controller.previous,
            "play": controller.play,
            "pause": controller.pause,
            "play_pause": controller.play_pause,
            "next": controller.next,
            "stop": controller.stop,
        }
        callback = actions.get(action)
        if callback is not None:
            self._logger.debug("Control multimedia: %s", action)
            callback()

    def nativeEvent(self, event_type: object, message: object) -> tuple[bool, int]:  # noqa: N802
        """Atiende WM_HOTKEY y teclados que envían WM_APPCOMMAND."""
        if (
            self._windows_media_session is not None
            and self._windows_media_session.is_available
        ):
            return super().nativeEvent(event_type, message)
        if sys.platform == "win32":
            try:
                import ctypes.wintypes

                native_message = ctypes.wintypes.MSG.from_address(int(message))
                action = None
                if native_message.message == 0x0312:  # WM_HOTKEY
                    action = self._media_hotkey_ids.get(int(native_message.wParam))
                elif native_message.message == 0x0319:  # WM_APPCOMMAND
                    command = (int(native_message.lParam) >> 16) & 0x7FF
                    action = {
                        11: "next",
                        12: "previous",
                        13: "stop",
                        14: "play_pause",
                    }.get(command)
                if action:
                    self._queue_media_action(action)
                    return True, 0
            except (TypeError, ValueError):
                pass
        return super().nativeEvent(event_type, message)

    def eventFilter(self, watched: object, event: QEvent) -> bool:  # noqa: N802 - Qt
        if isinstance(event, QMouseEvent):
            local_position = self.mapFromGlobal(event.globalPosition().toPoint())
            in_drag_zone = 0 <= local_position.y() <= 58
            interactive = self._is_interactive_widget(watched)
            resize_edges = self._resize_edges(local_position)

            if (
                event.type() == QEvent.Type.MouseMove
                and event.buttons() == Qt.MouseButton.NoButton
            ):
                cursor = self._cursor_for_edges(resize_edges)
                if cursor != self._resize_cursor:
                    self._resize_cursor = cursor
                    self.setCursor(cursor)

            if (
                event.type() == QEvent.Type.MouseButtonPress
                and event.button() == Qt.MouseButton.LeftButton
            ):
                handle = self.windowHandle()
                if handle is not None and resize_edges:
                    handle.startSystemResize(resize_edges)
                    return True
                if interactive or not in_drag_zone:
                    return super().eventFilter(watched, event)
                if handle is not None:
                    handle.startSystemMove()
                    return True
            if (
                event.type() == QEvent.Type.MouseButtonDblClick
                and event.button() == Qt.MouseButton.LeftButton
                and in_drag_zone
                and not interactive
            ):
                self._toggle_maximized()
                return True
        return super().eventFilter(watched, event)

    def _is_interactive_widget(self, watched: object) -> bool:
        widget = watched if isinstance(watched, QWidget) else None
        interactive_types = (
            QAbstractButton,
            QAbstractItemView,
            QLineEdit,
            QSlider,
            QScrollBar,
        )
        while widget is not None and widget is not self:
            if isinstance(widget, interactive_types):
                return True
            widget = widget.parentWidget()
        return False

    def _resize_edges(self, position: object) -> Qt.Edges:
        if self.isMaximized():
            return Qt.Edges()
        point = position
        edges = Qt.Edges()
        if point.x() <= self.RESIZE_MARGIN:
            edges |= Qt.Edge.LeftEdge
        elif point.x() >= self.width() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.RightEdge
        if point.y() <= self.RESIZE_MARGIN:
            edges |= Qt.Edge.TopEdge
        elif point.y() >= self.height() - self.RESIZE_MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    @staticmethod
    def _cursor_for_edges(edges: Qt.Edges) -> Qt.CursorShape:
        if edges in (
            Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
            Qt.Edge.RightEdge | Qt.Edge.BottomEdge,
        ):
            return Qt.CursorShape.SizeFDiagCursor
        if edges in (
            Qt.Edge.RightEdge | Qt.Edge.TopEdge,
            Qt.Edge.LeftEdge | Qt.Edge.BottomEdge,
        ):
            return Qt.CursorShape.SizeBDiagCursor
        if edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeHorCursor
        if edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt
        super().resizeEvent(event)
        if hasattr(self, "_loading_banner"):
            self._loading_banner.center_banner()
        if hasattr(self, "window_controls"):
            self.window_controls.move(
                max(0, self.width() - self.window_controls.width() - 10), 5
            )
            self.window_controls.raise_()
        if self.isMaximized():
            self._mask_timer.stop()
            self.clearMask()
        else:
            self.clearMask()
            self._mask_timer.start()

    def _apply_window_mask(self) -> None:
        if self.isMaximized() or self.isFullScreen():
            self.clearMask()
            return
        path = QPainterPath()
        path.addRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5))
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - nombre definido por Qt
        self._loading_banner.stop()
        if self._windows_media_session is not None:
            self._windows_media_session.shutdown()
        self._unregister_media_hotkeys()
        self._flush_listening_time()
        self._settings.setValue("window/geometry", self.saveGeometry())
        if self._player_controller is not None:
            self._player_controller.shutdown()
        super().closeEvent(event)
