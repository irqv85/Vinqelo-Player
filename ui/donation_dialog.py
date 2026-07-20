"""Opciones voluntarias para apoyar el desarrollo de Vinqelo."""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from config import ASSETS_DIR


BEP20_ADDRESS = "0x1e1f98f432b8d6fc063d67333223742725b48cef"
KOFI_URL = "https://ko-fi.com/irqv8"
QR_CROPS = {
    "binance_pay.jpg": QRect(202, 462, 364, 364),
    "usdt_bep20.jpg": QRect(255, 225, 510, 510),
    "btc_bep20.jpg": QRect(255, 225, 510, 510),
}


class DonationDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Apoyar Vinqelo")
        self.setModal(True)
        self.setObjectName("donationDialog")
        self.resize(680, 760)
        self.setMinimumSize(620, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 22)
        layout.setSpacing(14)

        title = QLabel("Apoyar el desarrollo de Vinqelo")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Las contribuciones son voluntarias y ayudan a mantener el proyecto. "
            "No desbloquean funciones adicionales."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.setObjectName("donationTabs")
        tabs.setDocumentMode(True)
        tabs.tabBar().setUsesScrollButtons(False)
        tabs.tabBar().setExpanding(True)
        tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        tabs.addTab(
            self._qr_tab(
                "binance_pay.jpg",
                "Escanea desde la aplicación de Binance",
            ),
            "Binance Pay",
        )
        tabs.addTab(
            self._wallet_tab(
                "usdt_bep20.jpg",
                "USDT",
                "Envía solamente USDT mediante BNB Smart Chain (BEP20).",
            ),
            "USDT · BEP20",
        )
        tabs.addTab(
            self._wallet_tab(
                "btc_bep20.jpg",
                "BTC",
                "Este depósito acepta BTC mediante BNB Smart Chain (BEP20), no Bitcoin por su red nativa.",
            ),
            "BTC · BEP20",
        )
        tabs.addTab(self._kofi_tab(), "Ko-fi")
        layout.addWidget(tabs, 1)

        close = QPushButton("Cerrar")
        close.setObjectName("donationSecondaryButton")
        close.setMinimumWidth(132)
        close.setFixedHeight(42)
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)

    def _qr_tab(self, filename: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        heading = QLabel("Binance Pay")
        heading.setObjectName("donationMethodTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image = self._qr_image(filename)
        text = QLabel(description)
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setObjectName("pageSubtitle")
        alias = QLabel("Perfil: IrQv8")
        alias.setObjectName("donationData")
        alias.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(image, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text)
        layout.addWidget(alias)
        return page

    def _wallet_tab(self, filename: str, currency: str, warning: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)
        heading = QLabel(f"{currency} · BNB Smart Chain (BEP20)")
        heading.setObjectName("donationMethodTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(self._qr_image(filename), 1, Qt.AlignmentFlag.AlignCenter)
        warning_label = QLabel(f"{currency}: {warning}")
        warning_label.setObjectName("donationWarning")
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)
        address_row = QHBoxLayout()
        address_row.setSpacing(10)
        address = QLineEdit(BEP20_ADDRESS)
        address.setObjectName("donationAddress")
        address.setReadOnly(True)
        address.setFixedHeight(42)
        copy = QPushButton("Copiar dirección")
        copy.setObjectName("donationPrimaryButton")
        copy.setMinimumWidth(164)
        copy.setFixedHeight(42)
        copy.setProperty("donationCopyButton", True)
        copy.clicked.connect(lambda: self._copy_address(copy))
        address_row.addWidget(address, 1)
        address_row.addWidget(copy)
        layout.addLayout(address_row)
        return page

    def _kofi_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 30, 24, 30)
        layout.addStretch(1)
        title = QLabel("Apoyar mediante Ko-fi")
        title.setObjectName("donationMethodTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description = QLabel(
            "Abre la página oficial de Vinqelo en Ko-fi para realizar un aporte."
        )
        description.setObjectName("pageSubtitle")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link = QLabel("ko-fi.com/irqv8")
        link.setObjectName("donationData")
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        open_button = QPushButton("Abrir Ko-fi")
        open_button.setObjectName("donationPrimaryButton")
        open_button.setMinimumWidth(180)
        open_button.setFixedHeight(44)
        open_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(KOFI_URL))
        )
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(link)
        layout.addWidget(open_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        return page

    @staticmethod
    def _qr_image(filename: str) -> QLabel:
        label = QLabel()
        label.setObjectName("donationQr")
        label.setFixedSize(320, 320)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(ASSETS_DIR / "donations" / filename))
        if not pixmap.isNull():
            crop = QR_CROPS.get(filename, pixmap.rect()).intersected(pixmap.rect())
            qr = pixmap.copy(crop)
            label.setPixmap(
                qr.scaled(
                    300,
                    300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation,
                )
            )
        else:
            label.setText("QR no disponible")
        return label

    @staticmethod
    def _copy_address(button: QPushButton) -> None:
        QApplication.clipboard().setText(BEP20_ADDRESS)
        button.setText("Dirección copiada")
        QTimer.singleShot(1500, lambda: button.setText("Copiar dirección"))
