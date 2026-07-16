"""Pagina de estado vacio para secciones sin contenido."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class EmptyPage(QWidget):
    def __init__(self, title: str, subtitle: str, empty_message: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 30, 38, 30)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(24)

        empty_card = QFrame()
        empty_card.setObjectName("emptyCard")
        empty_layout = QVBoxLayout(empty_card)
        empty_layout.setContentsMargins(28, 44, 28, 44)
        message = QLabel(empty_message)
        message.setObjectName("mutedLabel")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        empty_layout.addWidget(message)
        layout.addWidget(empty_card)
        layout.addStretch(1)

