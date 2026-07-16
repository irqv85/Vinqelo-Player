"""Ventana principal de Vinqelo Player."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from player.controller import PlayerController, PlayerUnavailableError
from ui.pages.empty_page import EmptyPage
from ui.pages.library_page import LibraryPage
from ui.widgets.player_bar import PlayerBar
from ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self._database = database
        self._pages: dict[str, QWidget] = {}
        self._player_controller: PlayerController | None = None
        self._player_error_message = ""

        self.setWindowTitle("Vinqelo Player")
        self.setMinimumSize(960, 620)
        self.resize(1180, 760)

        root = QWidget()
        root.setObjectName("appRoot")
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
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
        self._add_page(
            "albums",
            EmptyPage("Álbumes", "Colecciones de un artista principal.", "Aún no hay álbumes importados."),
        )
        self._add_page(
            "compilations",
            EmptyPage(
                "Compilaciones",
                "Carpetas con canciones de varios artistas.",
                "Aún no hay compilaciones importadas.",
            ),
        )
        self._add_page(
            "folders",
            EmptyPage("Carpetas", "Origen físico de tu biblioteca.", "Aún no hay carpetas importadas."),
        )
        self._add_page(
            "queue",
            EmptyPage(
                "Cola de reproducción",
                "Orden actual de escucha.",
                "La cola esta vacia.",
            ),
        )

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.stack, 1)
        self.player_bar = PlayerBar()
        root_layout.addWidget(content, 1)
        root_layout.addWidget(self.player_bar)
        self.setCentralWidget(root)

        self.sidebar.section_selected.connect(self.show_section)
        self.library_page.add_folder_requested.connect(self.select_folder)
        self.player_bar.open_file_requested.connect(self.open_audio_file)
        self._initialize_player()
        self.show_section("library")

    def _initialize_player(self) -> None:
        try:
            controller = PlayerController(self)
        except PlayerUnavailableError as exc:
            self._player_error_message = str(exc)
            self._logger.error("Reproducción no disponible: %s", exc)
            self.player_bar.set_engine_available(False, "VLC no está disponible")
            return

        self._player_controller = controller
        self.player_bar.set_engine_available(True)
        controller.track_changed.connect(self.player_bar.set_track)
        controller.state_changed.connect(self.player_bar.set_playback_state)
        controller.position_changed.connect(self.player_bar.set_timing)
        controller.queue_navigation_changed.connect(self.player_bar.set_queue_navigation)
        controller.error_occurred.connect(self._show_player_error)

        self.player_bar.previous_requested.connect(controller.previous)
        self.player_bar.rewind_requested.connect(lambda: controller.skip(-10))
        self.player_bar.play_pause_requested.connect(controller.play_pause)
        self.player_bar.stop_requested.connect(controller.stop)
        self.player_bar.forward_requested.connect(lambda: controller.skip(10))
        self.player_bar.next_requested.connect(controller.next)
        self.player_bar.seek_requested.connect(controller.seek_to)
        self.player_bar.volume_changed.connect(controller.set_volume)
        controller.set_volume(self.player_bar.volume.value())

    def _add_page(self, key: str, page: QWidget) -> None:
        self._pages[key] = page
        self.stack.addWidget(page)

    def show_section(self, section: str) -> None:
        page = self._pages.get(section)
        if page is not None:
            self.stack.setCurrentWidget(page)
            self.sidebar.select(section, emit_signal=False)

    def select_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            "Agregar carpeta a la biblioteca",
            str(Path.home() / "Music"),
        )
        if not selected:
            return

        folder_path = Path(selected)
        if not folder_path.exists() or not folder_path.is_dir():
            self._logger.warning("Se intentó seleccionar una carpeta inválida: %s", folder_path)
            QMessageBox.warning(self, "Carpeta no valida", "La carpeta seleccionada ya no existe.")
            return

        self.library_page.show_selected_folder(folder_path)
        self._logger.info("Carpeta seleccionada para futura importacion: %s", folder_path)

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
        self._player_controller.open_file(Path(selected))

    def _show_player_error(self, message: str) -> None:
        self._logger.error("Error de reproducción: %s", message)
        QMessageBox.warning(self, "No se pudo reproducir", message)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - nombre definido por Qt
        if self._player_controller is not None:
            self._player_controller.shutdown()
        super().closeEvent(event)
