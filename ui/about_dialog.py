"""Información de autoría y licencia de Vinqelo Player."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import (
    APP_AUTHOR,
    APP_AUTHOR_EMAIL,
    APP_LICENSE,
    APP_NAME,
    APP_VERSION,
    ASSETS_DIR,
    LICENSE_PATH,
)


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        heading = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(72, 72)
        pixmap = QPixmap(str(ASSETS_DIR / "icons" / "vinqelo-v.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    logo.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        identity = QVBoxLayout()
        name = QLabel(APP_NAME)
        name.setObjectName("pageTitle")
        version = QLabel(f"Versión {APP_VERSION}")
        version.setObjectName("pageSubtitle")
        identity.addStretch(1)
        identity.addWidget(name)
        identity.addWidget(version)
        identity.addStretch(1)
        heading.addWidget(logo)
        heading.addLayout(identity, 1)
        layout.addLayout(heading)

        details = QLabel(
            f"Desarrollado por <b>{APP_AUTHOR}</b><br>"
            f"{APP_AUTHOR_EMAIL}<br><br>"
            f"Licencia: <b>{APP_LICENSE}</b><br>"
            f"Copyright © 2026 {APP_AUTHOR}.<br><br>"
            "Software libre, distribuido sin garantía, conforme a los términos de la licencia."
        )
        details.setTextFormat(Qt.TextFormat.RichText)
        details.setWordWrap(True)
        layout.addWidget(details)

        self.license_text = QPlainTextEdit()
        self.license_text.setObjectName("aboutLicenseText")
        self.license_text.setReadOnly(True)
        self.license_text.setPlainText(self._read_license())
        self.license_text.setMinimumHeight(260)
        self.license_text.setVisible(False)
        layout.addWidget(self.license_text)

        buttons = QHBoxLayout()
        self.license_button = QPushButton("Ver licencia completa")
        self.license_button.setObjectName("secondaryButton")
        self.license_button.clicked.connect(self._toggle_license)
        close_button = QPushButton("Cerrar")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(self.license_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    @staticmethod
    def _read_license() -> str:
        try:
            return LICENSE_PATH.read_text(encoding="utf-8")
        except OSError:
            return "GNU General Public License, versión 3.0."

    def _toggle_license(self) -> None:
        visible = not self.license_text.isVisible()
        self.license_text.setVisible(visible)
        self.license_button.setText(
            "Ocultar licencia" if visible else "Ver licencia completa"
        )
        self.adjustSize()
