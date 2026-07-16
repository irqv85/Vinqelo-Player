"""Barra lateral de navegacion."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class Sidebar(QFrame):
    section_selected = Signal(str)

    SECTIONS = (
        ("library", "Biblioteca"),
        ("albums", "Álbumes"),
        ("compilations", "Compilaciones"),
        ("folders", "Carpetas"),
        ("queue", "Cola de reproducción"),
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(238)
        self._buttons: dict[str, QPushButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(7)

        brand = QLabel("Vinqelo Player")
        brand.setObjectName("brandName")
        caption = QLabel("Tu música, en un solo lugar")
        caption.setObjectName("brandCaption")
        layout.addWidget(brand)
        layout.addWidget(caption)
        layout.addSpacing(26)

        for key, label in self.SECTIONS:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, section=key: self.select(section))
            layout.addWidget(button)
            self._buttons[key] = button

        layout.addStretch(1)
        version_label = QLabel("Versión inicial 0.1.0")
        version_label.setObjectName("mutedLabel")
        layout.addWidget(version_label)

        self.select("library", emit_signal=False)

    def select(self, section: str, *, emit_signal: bool = True) -> None:
        if section not in self._buttons:
            return
        for key, button in self._buttons.items():
            button.setProperty("active", key == section)
            button.style().unpolish(button)
            button.style().polish(button)
        if emit_signal:
            self.section_selected.emit(section)
