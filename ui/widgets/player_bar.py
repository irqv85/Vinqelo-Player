"""Barra inferior de transporte y pista actual."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import ASSETS_DIR
from library.track_metadata import TrackDetails
from ui.icons import navigation_icon, transport_icon


class PlayerBar(QFrame):
    previous_requested = Signal()
    play_pause_requested = Signal()
    stop_requested = Signal()
    next_requested = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)
    effects_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playerBar")
        self.setFixedHeight(154)
        self._seeking = False
        self._current_file = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 11, 18, 11)
        layout.setSpacing(20)

        track_panel = QFrame()
        track_panel.setObjectName("trackPanel")
        track_panel.setFixedWidth(500)
        track_panel_layout = QHBoxLayout(track_panel)
        track_panel_layout.setContentsMargins(8, 8, 11, 8)
        track_panel_layout.setSpacing(11)

        self.cover_label = QLabel()
        self.cover_label.setObjectName("coverThumb")
        self.cover_label.setFixedSize(112, 112)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_default_cover()

        track_text = QWidget()
        track_text.setFixedWidth(340)
        track_layout = QVBoxLayout(track_text)
        track_layout.setContentsMargins(0, 1, 0, 1)
        track_layout.setSpacing(3)
        self.title_label = QLabel("Ninguna pista seleccionada")
        self.title_label.setObjectName("trackTitle")
        self.artist_label = QLabel("Abre un archivo para comenzar")
        self.artist_label.setObjectName("trackArtist")
        self.album_label = QLabel("Álbum desconocido")
        self.album_label.setObjectName("trackAlbum")
        self.catalog_label = QLabel("")
        self.catalog_label.setObjectName("trackMeta")
        self.quality_label = QLabel("TIPO Y CALIDAD DEL ARCHIVO")
        self.quality_label.setObjectName("trackQuality")
        track_layout.addWidget(self.title_label)
        track_layout.addWidget(self.artist_label)
        track_layout.addWidget(self.album_label)
        track_layout.addWidget(self.catalog_label)
        track_layout.addWidget(self.quality_label)
        track_layout.addStretch(1)

        track_panel_layout.addWidget(self.cover_label)
        track_panel_layout.addWidget(track_text, 1)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(5)

        button_row = QHBoxLayout()
        button_row.setSpacing(7)
        button_row.addStretch(1)

        self.previous_button = self._control_button("previous", "Pista anterior")
        self.play_button = self._control_button("play", "Reproducir o pausar", play=True)
        self.stop_button = self._control_button("stop", "Detener")
        self.next_button = self._control_button("next", "Pista siguiente")
        self.effects_button = QPushButton()
        self.effects_button.setObjectName("playerButton")
        self.effects_button.setIcon(navigation_icon("effects", "#e7edf7"))
        self.effects_button.setIconSize(QSize(20, 20))
        self.effects_button.setToolTip("Efectos: preamplificador y tempo")

        for button in (
            self.previous_button,
            self.play_button,
            self.next_button,
            self.stop_button,
            self.effects_button,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)

        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.play_button.clicked.connect(self.play_pause_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.effects_button.clicked.connect(self.effects_requested.emit)

        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(8)
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("mutedLabel")
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("mutedLabel")
        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.setEnabled(False)
        self.timeline.sliderPressed.connect(self._start_seeking)
        self.timeline.sliderMoved.connect(self._preview_seek)
        self.timeline.sliderReleased.connect(self._finish_seeking)
        timeline_row.addWidget(self.current_time_label)
        timeline_row.addWidget(self.timeline, 1)
        timeline_row.addWidget(self.duration_label)

        controls_layout.addLayout(button_row)
        controls_layout.addLayout(timeline_row)

        volume_box = QWidget()
        volume_layout = QVBoxLayout(volume_box)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.setSpacing(5)
        volume_title = QLabel("VOLUMEN")
        volume_title.setObjectName("columnHeader")
        volume_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_row = QHBoxLayout()
        volume_label = QLabel("VOL")
        volume_label.setObjectName("columnHeader")
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setFixedWidth(105)
        self.volume.valueChanged.connect(self.volume_changed.emit)
        volume_row.addWidget(volume_label)
        volume_row.addWidget(self.volume)
        volume_layout.addStretch(1)
        volume_layout.addWidget(volume_title)
        volume_layout.addLayout(volume_row)
        volume_layout.addStretch(1)

        layout.addWidget(track_panel)
        layout.addWidget(controls, 1)
        layout.addWidget(volume_box)

        self.set_track_available(False)
        self.set_queue_navigation(False, False)

    def _control_button(self, icon_kind: str, tooltip: str, *, play: bool = False) -> QPushButton:
        button = QPushButton()
        button.setObjectName("playButton" if play else "playerButton")
        button.setIcon(transport_icon(icon_kind))
        button.setIconSize(QSize(25, 25) if play else QSize(20, 20))
        button.setToolTip(tooltip)
        return button

    def set_track(self, title: str, artist: str, _file_path: str) -> None:
        self._current_file = _file_path
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.title_label.setToolTip(title)
        self.artist_label.setToolTip(artist)
        self.set_track_available(True)

    def set_track_details(self, details: TrackDetails) -> None:
        self._current_file = str(details.file_path)
        self.title_label.setText(details.title)
        self.artist_label.setText(details.artist)
        self.album_label.setText(details.album_line)
        self.catalog_label.setText(details.catalog_line)
        self.catalog_label.setVisible(bool(details.catalog_line))
        self.quality_label.setText(details.quality_line)
        tooltip = details.tooltip_text
        for label in (
            self.title_label,
            self.artist_label,
            self.album_label,
            self.catalog_label,
            self.quality_label,
        ):
            label.setToolTip(tooltip)
        self.set_track_available(True)
        # La portada oficial en línea tiene prioridad sobre imágenes incrustadas
        # con publicidad. El servicio de carátulas emitirá la imagen local solo
        # como respaldo cuando no encuentre el lanzamiento en internet.
        self._set_default_cover()
        self.cover_label.setToolTip("Buscando carátula oficial…")

    def set_cover_data(self, file_path: str, data: bytes, source: str) -> None:
        if file_path != self._current_file:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        target_size = self.cover_label.size()
        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - target_size.width()) // 2)
        y = max(0, (scaled.height() - target_size.height()) // 2)
        self.cover_label.setPixmap(scaled.copy(x, y, target_size.width(), target_size.height()))
        self.cover_label.setToolTip(source or "Carátula del álbum")

    def set_cover_unavailable(self, file_path: str) -> None:
        if file_path == self._current_file:
            self._set_default_cover()
            self.cover_label.setToolTip("No se encontró una carátula para este álbum")

    def _set_default_cover(self) -> None:
        cover = QPixmap(str(ASSETS_DIR / "icons" / "vinqelo-v.png"))
        if cover.isNull():
            self.cover_label.clear()
            return
        self.cover_label.setPixmap(
            cover.scaled(
                72,
                72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_track_available(self, available: bool) -> None:
        for button in (
            self.play_button,
            self.stop_button,
        ):
            button.setEnabled(available)
        self.timeline.setEnabled(available)

    def set_engine_available(self, available: bool, message: str = "") -> None:
        self.volume.setEnabled(available)
        self.effects_button.setEnabled(available)
        if not available:
            self.set_track_available(False)
            self.artist_label.setText(message or "VLC no está disponible")

    def set_playback_state(self, state: str) -> None:
        if state == "playing":
            self.play_button.setIcon(transport_icon("pause"))
            self.play_button.setToolTip("Pausar")
        else:
            self.play_button.setIcon(transport_icon("play"))
            self.play_button.setToolTip("Reproducir")

    def set_queue_navigation(self, has_previous: bool, has_next: bool) -> None:
        self.previous_button.setEnabled(has_previous or self.timeline.isEnabled())
        self.next_button.setEnabled(has_next)

    def set_timing(self, current_ms: int, duration_ms: int) -> None:
        current_ms = max(0, current_ms)
        duration_ms = max(0, duration_ms)
        if not self._seeking:
            self.timeline.setRange(0, max(0, duration_ms))
            self.timeline.setValue(min(current_ms, duration_ms) if duration_ms else 0)
            self.current_time_label.setText(format_milliseconds(current_ms))
        self.duration_label.setText(format_milliseconds(duration_ms))

    def _start_seeking(self) -> None:
        self._seeking = True

    def _preview_seek(self, value: int) -> None:
        self.current_time_label.setText(format_milliseconds(value))

    def _finish_seeking(self) -> None:
        self._seeking = False
        self.seek_requested.emit(self.timeline.value())


def format_milliseconds(milliseconds: int) -> str:
    total_seconds = max(0, int(milliseconds)) // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
