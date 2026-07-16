"""Barra inferior y controles de reproducción."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class PlayerBar(QFrame):
    open_file_requested = Signal()
    previous_requested = Signal()
    rewind_requested = Signal()
    play_pause_requested = Signal()
    stop_requested = Signal()
    forward_requested = Signal()
    next_requested = Signal()
    seek_requested = Signal(int)
    volume_changed = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("playerBar")
        self.setFixedHeight(116)
        self._seeking = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 13, 24, 13)
        layout.setSpacing(22)

        track_info = QWidget()
        track_layout = QVBoxLayout(track_info)
        track_layout.setContentsMargins(0, 0, 0, 0)
        track_layout.setSpacing(4)
        self.title_label = QLabel("Ninguna pista seleccionada")
        self.artist_label = QLabel("Abre un archivo para comenzar")
        self.artist_label.setObjectName("trackArtist")
        self.open_button = QPushButton("Abrir archivo")
        self.open_button.setObjectName("secondaryButton")
        self.open_button.setFixedWidth(112)
        self.open_button.clicked.connect(self.open_file_requested.emit)
        track_layout.addWidget(self.title_label)
        track_layout.addWidget(self.artist_label)
        track_layout.addWidget(self.open_button)
        track_info.setMinimumWidth(240)
        track_info.setMaximumWidth(280)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(7)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch(1)

        self.previous_button = self._control_button("|<", "Pista anterior")
        self.rewind_button = self._control_button("-10", "Retroceder 10 segundos")
        self.play_button = self._control_button(">", "Reproducir o pausar")
        self.stop_button = self._control_button("■", "Detener")
        self.forward_button = self._control_button("+10", "Avanzar 10 segundos")
        self.next_button = self._control_button(">|", "Pista siguiente")

        for button in (
            self.previous_button,
            self.rewind_button,
            self.play_button,
            self.stop_button,
            self.forward_button,
            self.next_button,
        ):
            button_row.addWidget(button)
        button_row.addStretch(1)

        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.rewind_button.clicked.connect(self.rewind_requested.emit)
        self.play_button.clicked.connect(self.play_pause_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.forward_button.clicked.connect(self.forward_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)

        timeline_row = QHBoxLayout()
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
        volume_layout = QHBoxLayout(volume_box)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_label = QLabel("Vol.")
        volume_label.setObjectName("mutedLabel")
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setFixedWidth(100)
        self.volume.valueChanged.connect(self.volume_changed.emit)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume)

        layout.addWidget(track_info)
        layout.addWidget(controls, 1)
        layout.addWidget(volume_box)

        self.set_track_available(False)
        self.set_queue_navigation(False, False)

    def _control_button(self, text: str, tooltip: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("playerButton")
        button.setToolTip(tooltip)
        return button

    def set_track(self, title: str, artist: str, _file_path: str) -> None:
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.title_label.setToolTip(title)
        self.artist_label.setToolTip(artist)
        self.set_track_available(True)

    def set_track_available(self, available: bool) -> None:
        for button in (
            self.rewind_button,
            self.play_button,
            self.stop_button,
            self.forward_button,
        ):
            button.setEnabled(available)
        self.timeline.setEnabled(available)

    def set_engine_available(self, available: bool, message: str = "") -> None:
        self.open_button.setEnabled(available)
        self.volume.setEnabled(available)
        if not available:
            self.set_track_available(False)
            self.artist_label.setText(message or "VLC no está disponible")

    def set_playback_state(self, state: str) -> None:
        if state == "playing":
            self.play_button.setText("||")
            self.play_button.setToolTip("Pausar")
        else:
            self.play_button.setText(">")
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
