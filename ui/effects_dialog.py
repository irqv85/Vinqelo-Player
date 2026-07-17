"""Consola compacta de preamplificador y ecualizador VLC."""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, QSettings, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)

from player.controller import PlayerController


FREQUENCIES = (31.25, 62.5, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0)
DEFAULT_BANDS = (1, 2, 4, 5, 7, 9)


def frequency_label(value: float) -> str:
    if value >= 1000:
        return f"{value / 1000:g} kHz"
    return f"{value:g} Hz"


class VerticalLedMeter(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._level = 0.5
        self._playing = False
        self._phase = 0.0
        self.setFixedWidth(22)
        self.setMinimumHeight(250)
        self._animation = QTimer(self)
        self._animation.setInterval(80)
        self._animation.timeout.connect(self._tick)

    def set_decibels(self, value: float) -> None:
        self._level = max(0.0, min(1.0, (float(value) + 20.0) / 40.0))
        self.update()

    def set_playing(self, state: str) -> None:
        self._playing = state == "playing"
        if self._playing:
            self._animation.start()
        else:
            self._animation.stop()
            self.update()

    def _tick(self) -> None:
        self._phase += 0.62
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#070b0f"))
        count, gap = 22, 2.0
        height = (self.height() - 16 - gap * (count - 1)) / count
        level = self._level
        if self._playing:
            wave = 0.11 * math.sin(self._phase) + 0.045 * math.sin(self._phase * 2.6)
            level = max(0.05, min(1.0, 0.18 + self._level * 0.70 + wave))
        lit = round(level * count)
        for index in range(count):
            ratio = index / (count - 1)
            color = QColor(
                "#42e675" if ratio < 0.68 else "#ffc43d" if ratio < 0.87 else "#ff4f49"
            )
            if index >= lit:
                color.setAlpha(28)
            y = self.height() - 8 - (index + 1) * height - index * gap
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(4, y, self.width() - 8, height), 1.5, 1.5)


class EffectsDialog(QDialog):
    RECOMMENDED_LIMIT = 60

    def __init__(self, controller: PlayerController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.settings = QSettings("Vinqelo", "Vinqelo Player")
        self._detent_armed = True
        self._block_preamp_drag = False
        self._detent_triggered = False
        self.band_sliders: list[QSlider] = []
        self.band_spins: list[QDoubleSpinBox] = []
        self.frequency_boxes: list[QComboBox] = []
        self.setWindowTitle("Efectos · Vinqelo Player")
        self.setMinimumSize(900, 550)
        self.setModal(False)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)
        title = QLabel("Consola de sonido")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Preamplificador y ecualizador configurable de 6 bandas sobre VLC.")
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        console = QFrame()
        console.setObjectName("mixerConsole")
        console_layout = QHBoxLayout(console)
        console_layout.setContentsMargins(14, 14, 14, 14)
        console_layout.setSpacing(10)

        self.preamp_slider, self.preamp_spin = self._create_channel(
            console_layout, "PREAMP", "GAIN", accent=True
        )
        led_box = QFrame()
        led_box.setObjectName("vuChannel")
        led_layout = QVBoxLayout(led_box)
        led_layout.setContentsMargins(5, 8, 5, 8)
        led_title = QLabel("VU")
        led_title.setObjectName("columnHeader")
        led_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.meter = VerticalLedMeter()
        led_layout.addWidget(led_title)
        led_layout.addWidget(self.meter, 1, Qt.AlignmentFlag.AlignHCenter)
        console_layout.addWidget(led_box)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setObjectName("mixerSeparator")
        console_layout.addWidget(separator)

        for number in range(6):
            slider, spin = self._create_channel(
                console_layout, f"BAND {number + 1}", "", accent=False
            )
            combo = QComboBox()
            combo.setObjectName("frequencySelector")
            for index, frequency in enumerate(FREQUENCIES):
                combo.addItem(frequency_label(frequency), index)
            combo.setCurrentIndex(DEFAULT_BANDS[number])
            combo.setProperty("previousBand", DEFAULT_BANDS[number])
            combo.currentIndexChanged.connect(
                lambda _index, active=combo: self._frequency_changed(active)
            )
            channel = slider.parentWidget()
            channel.layout().addWidget(combo)
            self.band_sliders.append(slider)
            self.band_spins.append(spin)
            self.frequency_boxes.append(combo)

        root.addWidget(console, 1)

        note = QLabel(
            "El Preamp ofrece −20 a +20 dB y se detiene primero en +6 dB. "
            "Suelta y vuelve a moverlo para superar ese punto."
        )
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
        root.addWidget(note)

        buttons = QHBoxLayout()
        reset = QPushButton("Restablecer consola")
        reset.setObjectName("effectSecondaryButton")
        reset.clicked.connect(self._reset)
        close = QPushButton("Cerrar")
        close.setObjectName("primaryButton")
        close.clicked.connect(self.close)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(close)
        root.addLayout(buttons)

        self._apply_timer = QTimer(self)
        self._apply_timer.setSingleShot(True)
        self._apply_timer.setInterval(90)
        self._apply_timer.timeout.connect(self._apply)
        self.preamp_slider.sliderPressed.connect(self._preamp_pressed)
        self.preamp_slider.sliderReleased.connect(self._preamp_released)
        self.controller.state_changed.connect(self.meter.set_playing)
        self.meter.set_playing(self.controller.state.value)
        self._load()

    def _create_channel(
        self, layout: QHBoxLayout, name: str, footer: str, *, accent: bool
    ) -> tuple[QSlider, QDoubleSpinBox]:
        frame = QFrame()
        frame.setObjectName("mixerPreamp" if accent else "mixerChannel")
        frame.setMinimumWidth(96)
        box = QVBoxLayout(frame)
        box.setContentsMargins(8, 9, 8, 9)
        box.setSpacing(6)
        label = QLabel(name)
        label.setObjectName("columnHeader")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scale = QHBoxLayout()
        marks = QVBoxLayout()
        for text_value in ("+20", "+10", "0", "−10", "−20"):
            mark = QLabel(text_value)
            mark.setObjectName("mixerScale")
            marks.addWidget(mark)
            if text_value != "−20":
                marks.addStretch(1)
        slider = QSlider(Qt.Orientation.Vertical)
        slider.setObjectName("mixerFader")
        slider.setRange(-200, 200)
        slider.setValue(0)
        slider.setTickInterval(20)
        scale.addLayout(marks)
        scale.addWidget(slider, 1, Qt.AlignmentFlag.AlignHCenter)
        spin = QDoubleSpinBox()
        spin.setObjectName("mixerValue")
        spin.setRange(-20.0, 20.0)
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setSuffix(" dB")
        footer_label = QLabel(footer)
        footer_label.setObjectName("mixerFooter")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(label)
        box.addLayout(scale, 1)
        box.addWidget(spin)
        if footer:
            box.addWidget(footer_label)
        slider.valueChanged.connect(
            lambda value, active_slider=slider, active_spin=spin:
            self._from_slider(active_slider, active_spin, value)
        )
        spin.valueChanged.connect(
            lambda value, active_slider=slider: self._from_spin(active_slider, value)
        )
        layout.addWidget(frame, 1)
        return slider, spin

    def _load(self) -> None:
        for obsolete in (
            "effects/playback_rate", "effects/auto_preamp", "effects/low_db",
            "effects/high_db", "effects/treble_db",
        ):
            self.settings.remove(obsolete)
        self.preamp_slider.setValue(
            round(float(self.settings.value("effects/preamp_db", 0.0)) * 10)
        )
        for number, (slider, combo) in enumerate(
            zip(self.band_sliders, self.frequency_boxes)
        ):
            slider.setValue(
                round(float(self.settings.value(f"effects/band_{number}_db", 0.0)) * 10)
            )
            band = int(self.settings.value(f"effects/band_{number}_frequency", DEFAULT_BANDS[number]))
            band = max(0, min(len(FREQUENCIES) - 1, band))
            combo.setCurrentIndex(band)
            combo.setProperty("previousBand", band)
        self._apply()

    def _frequency_changed(self, changed: QComboBox) -> None:
        new_band = int(changed.currentData())
        old_band = int(changed.property("previousBand") or 0)
        for other in self.frequency_boxes:
            if other is changed or int(other.currentData()) != new_band:
                continue
            other.blockSignals(True)
            other.setCurrentIndex(old_band)
            other.setProperty("previousBand", old_band)
            other.blockSignals(False)
            break
        changed.setProperty("previousBand", new_band)
        self._apply_timer.start()

    def _preamp_pressed(self) -> None:
        self._block_preamp_drag = (
            self._detent_armed and self.preamp_slider.value() <= self.RECOMMENDED_LIMIT
        )
        self._detent_triggered = False

    def _preamp_released(self) -> None:
        if self._detent_triggered:
            self._detent_armed = False
        elif self.preamp_slider.value() <= self.RECOMMENDED_LIMIT:
            self._detent_armed = True
        self._block_preamp_drag = False

    def _from_slider(
        self, slider: QSlider, spin: QDoubleSpinBox, value: int
    ) -> None:
        if (
            slider is self.preamp_slider
            and self._block_preamp_drag
            and value > self.RECOMMENDED_LIMIT
        ):
            self._detent_triggered = True
            slider.blockSignals(True)
            slider.setValue(self.RECOMMENDED_LIMIT)
            slider.blockSignals(False)
            value = self.RECOMMENDED_LIMIT
        spin.blockSignals(True)
        spin.setValue(value / 10.0)
        spin.blockSignals(False)
        if slider is self.preamp_slider:
            self.meter.set_decibels(value / 10.0)
        self._apply_timer.start()

    def _from_spin(self, slider: QSlider, value: float) -> None:
        slider.setValue(round(value * 10))
        if slider is self.preamp_slider and value > 6.0:
            self._detent_armed = False

    def _apply(self) -> None:
        preamp = self.preamp_slider.value() / 10.0
        bands = [
            (int(combo.currentData()), slider.value() / 10.0)
            for slider, combo in zip(self.band_sliders, self.frequency_boxes)
        ]
        self.controller.set_preamp(preamp)
        self.controller.set_equalizer_bands(bands)
        self.settings.setValue("effects/preamp_db", preamp)
        for number, ((band, gain), combo) in enumerate(zip(bands, self.frequency_boxes)):
            self.settings.setValue(f"effects/band_{number}_db", gain)
            self.settings.setValue(f"effects/band_{number}_frequency", band)

    def _reset(self) -> None:
        self.preamp_slider.setValue(0)
        for number, (slider, combo) in enumerate(
            zip(self.band_sliders, self.frequency_boxes)
        ):
            slider.setValue(0)
            combo.setCurrentIndex(DEFAULT_BANDS[number])
        self._detent_armed = True
        self._apply()
