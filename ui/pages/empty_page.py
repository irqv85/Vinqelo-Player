"""Vista de lista vacía para secciones de la biblioteca."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class EmptyPage(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str,
        empty_message: str,
        columns: tuple[str, ...] = ("NOMBRE", "ARTISTA", "PISTAS"),
    ) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(3)

        eyebrow = QLabel("BIBLIOTECA")
        eyebrow.setObjectName("pageEyebrow")
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        layout.addWidget(eyebrow)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(16)

        panel = QFrame()
        panel.setObjectName("emptyCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        table_header = QFrame()
        table_header.setObjectName("tableHeader")
        table_header.setFixedHeight(38)
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(18, 0, 18, 0)
        for column in columns:
            label = QLabel(column)
            label.setObjectName("columnHeader")
            table_header_layout.addWidget(label, 1)
        panel_layout.addWidget(table_header)

        empty_content = QWidget()
        empty_layout = QVBoxLayout(empty_content)
        empty_layout.setContentsMargins(28, 44, 28, 44)
        empty_layout.addStretch(1)
        message = QLabel(empty_message)
        message.setObjectName("mutedLabel")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        empty_layout.addWidget(message)
        empty_layout.addStretch(1)
        panel_layout.addWidget(empty_content, 1)

        layout.addWidget(panel, 1)
