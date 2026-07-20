"""Barra inferior de transporte y pista actual."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QStyle, QWidget,
)

from config import ASSETS_DIR
from library.track_metadata import TrackDetails
from ui.icons import navigation_icon, transport_icon
from ui.i18n import translate_text


class ClickableTrackPanel(QFrame):
    clicked = Signal()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class SeekSlider(QSlider):
    """Barra que permite saltar exactamente al punto pulsado."""

    jump_requested = Signal(int)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > self.minimum():
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(), round(event.position().x()), max(1, self.width())
            )
            self.setValue(value)
            self.jump_requested.emit(value)


class PlayerBar(QFrame):
    previous_requested = Signal()
    play_pause_requested = Signal()
    stop_requested = Signal()
    next_requested = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)
    effects_requested = Signal()
    now_playing_requested = Signal()
    repeat_mode_requested = Signal(str)
    shuffle_mode_requested = Signal(str)

    REPEAT_MODES = ("off", "one", "queue")
    SHUFFLE_MODES = ("off", "queue")

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playerBar")
        self.setFixedHeight(154)
        self._seeking = False
        self._current_file = ""
        self._current_details: TrackDetails | None = None
        self._cover_source = ""
        self._repeat_mode = "off"
        self._shuffle_mode = "off"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 11, 18, 11)
        layout.setSpacing(20)

        track_panel = ClickableTrackPanel()
        track_panel.setObjectName("trackPanel")
        track_panel.setFixedWidth(500)
        track_panel.setCursor(Qt.CursorShape.PointingHandCursor)
        track_panel.setToolTip("Ir a la pista en reproducción")
        track_panel.clicked.connect(self.now_playing_requested.emit)
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
        self.repeat_button = self._mode_button("repeat_all", "Repetición desactivada")
        self.shuffle_button = self._mode_button("shuffle", "Aleatorio desactivado")
        self.effects_button = QPushButton()
        self.effects_button.setObjectName("playerButton")
        self.effects_button.setIcon(navigation_icon("effects", "#e7edf7"))
        self.effects_button.setIconSize(QSize(20, 20))
        self.effects_button.setToolTip("Efectos: preamplificador y ecualizador")

        for button in (
            self.previous_button,
            self.play_button,
            self.next_button,
            self.stop_button,
            self.effects_button,
            self.repeat_button,
            self.shuffle_button,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)

        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.play_button.clicked.connect(self.play_pause_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.effects_button.clicked.connect(self.effects_requested.emit)
        self.repeat_button.clicked.connect(self._show_repeat_menu)
        self.shuffle_button.clicked.connect(self._show_shuffle_menu)

        timeline_row = QHBoxLayout()
        timeline_row.setSpacing(8)
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("mutedLabel")
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("mutedLabel")
        self.timeline = SeekSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.setEnabled(False)
        self.timeline.sliderPressed.connect(self._start_seeking)
        self.timeline.sliderMoved.connect(self._preview_seek)
        self.timeline.sliderReleased.connect(self._finish_seeking)
        self.timeline.jump_requested.connect(self.seek_requested.emit)
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

    def _mode_button(self, icon_kind: str, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName("modeButton")
        button.setFixedSize(28, 28)
        button.setIcon(transport_icon(icon_kind, "#8fa7c7", 20))
        button.setIconSize(QSize(17, 17))
        button.setToolTip(tooltip)
        button.setProperty("modeActive", False)
        return button

    def _show_repeat_menu(self) -> None:
        choices = (
            ("off", "Desactivado"),
            ("one", "Una pista"),
            ("queue", "Carpeta o lista actual"),
        )
        selected = self._mode_menu(self.repeat_button, choices, self._repeat_mode)
        if selected is not None:
            self.set_repeat_mode(selected)
            self.repeat_mode_requested.emit(selected)

    def _show_shuffle_menu(self) -> None:
        choices = (
            ("off", "Desactivado"),
            ("queue", "Carpeta o lista actual"),
        )
        selected = self._mode_menu(self.shuffle_button, choices, self._shuffle_mode)
        if selected is not None:
            self.set_shuffle_mode(selected)
            self.shuffle_mode_requested.emit(selected)

    def _mode_menu(
        self,
        button: QPushButton,
        choices: tuple[tuple[str, str], ...],
        current: str,
    ) -> str | None:
        menu = QMenu(self)
        actions = {}
        for mode, label in choices:
            action = menu.addAction(translate_text(label))
            action.setCheckable(True)
            action.setChecked(mode == current)
            actions[action] = mode
        selected = menu.exec(button.mapToGlobal(QPoint(0, button.height() + 4)))
        return actions.get(selected)

    def set_repeat_mode(self, mode: str) -> None:
        self._repeat_mode = mode if mode in self.REPEAT_MODES else "off"
        icons = {"off": "repeat_all", "one": "repeat_one", "queue": "repeat_album"}
        tips = {
            "off": "Repetición desactivada", "one": "Repetir una pista",
            "queue": "Repetir carpeta o lista actual",
        }
        self._update_mode_button(self.repeat_button, icons[self._repeat_mode], tips[self._repeat_mode], self._repeat_mode != "off")

    def set_shuffle_mode(self, mode: str) -> None:
        self._shuffle_mode = mode if mode in self.SHUFFLE_MODES else "off"
        icons = {"off": "shuffle", "queue": "shuffle_album"}
        tips = {
            "off": "Aleatorio desactivado", "queue": "Aleatorio en carpeta o lista actual",
        }
        self._update_mode_button(self.shuffle_button, icons[self._shuffle_mode], tips[self._shuffle_mode], self._shuffle_mode != "off")

    @staticmethod
    def _update_mode_button(button: QPushButton, icon_kind: str, tooltip: str, active: bool) -> None:
        button.setIcon(transport_icon(icon_kind, "#dce7f7" if active else "#70839f", 20))
        button.setToolTip(translate_text(tooltip))
        button.setProperty("modeActive", active)
        button.style().unpolish(button)
        button.style().polish(button)

    def set_track(self, title: str, artist: str, _file_path: str) -> None:
        self._current_file = _file_path
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.title_label.setToolTip(title)
        self.artist_label.setToolTip(artist)
        self.set_track_available(True)

    def set_track_details(self, details: TrackDetails) -> None:
        self._current_details = details
        self._current_file = str(details.file_path)
        self._render_track_details(details)
        self.set_track_available(True)
        # La portada oficial en línea tiene prioridad sobre imágenes incrustadas
        # con publicidad. El servicio de carátulas emitirá la imagen local solo
        # como respaldo cuando no encuentre el lanzamiento en internet.
        self._set_default_cover()
        self._cover_source = "Buscando carátula oficial…"
        self.cover_label.setToolTip(translate_text(self._cover_source))

    def _render_track_details(self, details: TrackDetails) -> None:
        self.title_label.setText(details.title)
        self.artist_label.setText(details.artist)
        self.album_label.setText(details.album_line)
        catalog_parts: list[str] = []
        if details.track_number:
            catalog_parts.append(f'{translate_text("Pista")} {details.track_number}')
        if details.disc_number:
            catalog_parts.append(f'{translate_text("Disco")} {details.disc_number}')
        if details.genre:
            catalog_parts.append(details.genre)
        catalog = "  ·  ".join(catalog_parts)
        self.catalog_label.setText(catalog)
        self.catalog_label.setVisible(bool(catalog))

        quality_parts = [details.file_format]
        if details.codec and details.codec.upper() != details.file_format.upper():
            quality_parts.append(details.codec)
        if details.bits_per_sample:
            quality_parts.append(
                f'{details.bits_per_sample} {translate_text("bits")}'
            )
        if details.sample_rate_hz:
            rate = (
                f"{details.sample_rate_hz // 1000} kHz"
                if details.sample_rate_hz % 1000 == 0
                else f"{details.sample_rate_hz / 1000:.1f} kHz"
            )
            quality_parts.append(rate)
        if details.bitrate_kbps:
            quality_parts.append(
                f'{details.bitrate_kbps:,} kbps'.replace(',', ' ')
            )
        if details.channels:
            channel = {
                1: translate_text("Mono"),
                2: translate_text("Estéreo"),
            }.get(
                details.channels,
                f'{details.channels} {translate_text("canales")}',
            )
            quality_parts.append(channel)
        quality = "  ·  ".join(quality_parts)
        self.quality_label.setText(quality)

        size_mb = details.size_bytes / (1024 * 1024)
        tooltip_lines = [
            f'{translate_text("Título")}: {details.title}',
            f'{translate_text("Artista")}: {details.artist}',
            f'{translate_text("Álbum")}: {details.album}',
            f'{translate_text("Artista del álbum")}: {details.album_artist}',
        ]
        if details.year:
            tooltip_lines.append(f'{translate_text("Año")}: {details.year}')
        if details.genre:
            tooltip_lines.append(f'{translate_text("Género")}: {details.genre}')
        if details.track_number:
            tooltip_lines.append(
                f'{translate_text("Pista")}: {details.track_number}'
            )
        tooltip_lines.extend(
            (
                f'{translate_text("Calidad")}: {quality}',
                f'{translate_text("Tamaño")}: {size_mb:.1f} MB',
            )
        )
        tooltip = "\n".join(tooltip_lines)
        for label in (
            self.title_label,
            self.artist_label,
            self.album_label,
            self.catalog_label,
            self.quality_label,
        ):
            label.setToolTip(tooltip)

    def retranslate_dynamic(self) -> None:
        """Vuelve a dibujar los metadatos variables al cambiar de idioma."""
        if self._current_details is not None:
            self._render_track_details(self._current_details)
        if self._cover_source:
            self.cover_label.setToolTip(
                self._translated_cover_source(self._cover_source)
            )

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
        self._cover_source = source or "Carátula del álbum"
        self.cover_label.setToolTip(
            self._translated_cover_source(self._cover_source)
        )

    def set_cover_unavailable(self, file_path: str) -> None:
        if file_path == self._current_file:
            self._set_default_cover()
            self._cover_source = "No se encontró una carátula para este álbum"
            self.cover_label.setToolTip(translate_text(self._cover_source))

    @staticmethod
    def _translated_cover_source(source: str) -> str:
        prefix = "Archivo local:"
        if source.startswith(prefix):
            return f'{translate_text("Archivo local")}: {source[len(prefix):].strip()}'
        return translate_text(source)

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
