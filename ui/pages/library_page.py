"""Vista general de la biblioteca."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from ui.widgets.stat_card import StatCard


class LibraryPage(QWidget):
    add_folder_requested = Signal()

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self._database = database

        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 30, 38, 30)
        layout.setSpacing(7)

        header = QHBoxLayout()
        text_box = QVBoxLayout()
        title = QLabel("Biblioteca")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Organiza tus carpetas como álbumes o compilaciones.")
        subtitle.setObjectName("pageSubtitle")
        text_box.addWidget(title)
        text_box.addWidget(subtitle)

        add_button = QPushButton("Agregar carpeta a la biblioteca")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_folder_requested.emit)
        header.addLayout(text_box, 1)
        header.addWidget(add_button)
        layout.addLayout(header)
        layout.addSpacing(18)

        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(12)
        self._stats = {
            "albums": StatCard("Álbumes"),
            "compilations": StatCard("Compilaciones"),
            "tracks": StatCard("Pistas"),
        }
        for column, card in enumerate(self._stats.values()):
            stats_layout.addWidget(card, 0, column)
        layout.addLayout(stats_layout)
        layout.addSpacing(18)

        empty_card = QFrame()
        empty_card.setObjectName("emptyCard")
        empty_layout = QVBoxLayout(empty_card)
        empty_layout.setContentsMargins(28, 36, 28, 36)
        empty_layout.setSpacing(8)
        empty_title = QLabel("Tu biblioteca está lista")
        empty_title.setStyleSheet("font-size: 18px; font-weight: 600;")
        empty_description = QLabel(
            "Selecciona una carpeta de música. En el siguiente bloque se agregará "
            "la detección y la pantalla de confirmación antes de importar."
        )
        empty_description.setObjectName("mutedLabel")
        empty_description.setWordWrap(True)
        self._selection_label = QLabel("")
        self._selection_label.setObjectName("mutedLabel")
        self._selection_label.setWordWrap(True)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_description)
        empty_layout.addWidget(self._selection_label)
        layout.addWidget(empty_card)
        layout.addStretch(1)

        self.refresh_stats()

    def refresh_stats(self) -> None:
        stats = self._database.get_library_stats()
        for key, card in self._stats.items():
            card.set_value(stats[key])

    def show_selected_folder(self, path: Path) -> None:
        self._selection_label.setText(f"Carpeta seleccionada: {path}")
