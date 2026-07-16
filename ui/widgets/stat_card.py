"""Tarjeta pequena para mostrar un conteo de biblioteca."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(92)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(3)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("statValue")
        caption = QLabel(label)
        caption.setObjectName("statLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(caption)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))

