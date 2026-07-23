"""Información de autoría y licencia de Vinqelo Player."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QPixmap
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
    PROJECT_URL,
)
from ui.donation_dialog import DonationDialog
from ui.i18n import translate_text


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle(f"{translate_text('Acerca de')} {APP_NAME}")
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
        version = QLabel(f"{translate_text('Versión')} {APP_VERSION}")
        version.setObjectName("pageSubtitle")
        identity.addStretch(1)
        identity.addWidget(name)
        identity.addWidget(version)
        identity.addStretch(1)
        heading.addWidget(logo)
        heading.addLayout(identity, 1)
        layout.addLayout(heading)

        details = QLabel(
            f"{translate_text('Desarrollado por')} <b>{APP_AUTHOR}</b><br>"
            f"{APP_AUTHOR_EMAIL}<br><br>"
            f"{translate_text('Licencia')}: <b>{APP_LICENSE}</b><br>"
            f"{translate_text('Código fuente')}: "
            f'<a style="color:#4b9aff" href="{PROJECT_URL}">'
            "github.com/irqv85/Vinqelo-Player</a><br>"
            f"Copyright © 2026 {APP_AUTHOR}.<br><br>"
            f"{translate_text('Software libre, distribuido sin garantía, conforme a los términos de la licencia.')}"
        )
        details.setObjectName("aboutDetails")
        details.setTextFormat(Qt.TextFormat.RichText)
        details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        details.setOpenExternalLinks(True)
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
        support_button = QPushButton("Apoyar Vinqelo")
        support_button.setObjectName("primaryButton")
        support_button.clicked.connect(self._show_donations)
        self.license_button = QPushButton("Ver licencia completa")
        self.license_button.setObjectName("secondaryButton")
        self.license_button.clicked.connect(self._toggle_license)
        github_button = QPushButton("GitHub")
        github_button.setObjectName("secondaryButton")
        github_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(PROJECT_URL))
        )
        close_button = QPushButton("Cerrar")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(support_button)
        buttons.addWidget(self.license_button)
        buttons.addWidget(github_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def _show_donations(self) -> None:
        DonationDialog(self).exec()

    @staticmethod
    def _read_license() -> str:
        try:
            return LICENSE_PATH.read_text(encoding="utf-8")
        except OSError:
            return translate_text("GNU General Public License, versión 3.0.")

    def _toggle_license(self) -> None:
        visible = not self.license_text.isVisible()
        self.license_text.setVisible(visible)
        self.license_button.setText(
            translate_text("Ocultar licencia") if visible
            else translate_text("Ver licencia completa")
        )
        self.adjustSize()
