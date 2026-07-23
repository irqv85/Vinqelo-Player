"""Banner compacto para el arranque y la sincronización de la biblioteca."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config import ASSETS_DIR
from ui.i18n import translate_text


class LoadingBanner(QFrame):
    """Muestra mensajes amables sin exponer detalles técnicos internos."""

    def __init__(self, parent: QWidget | None = None, *, startup: bool = False) -> None:
        flags = (
            Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint
            if startup
            else Qt.WindowType.Widget
        )
        super().__init__(parent, flags)
        self._startup = startup
        self._messages: list[str] = []
        self._message_index = 0
        self.setObjectName("loadingBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedSize(410, 164)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        panel = QFrame()
        panel.setObjectName("loadingBannerPanel")
        root.addWidget(panel)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 15, 18, 13)
        panel_layout.setSpacing(10)

        content = QHBoxLayout()
        content.setSpacing(14)
        logo = QLabel()
        logo.setObjectName("loadingBannerLogo")
        logo.setFixedSize(76, 76)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(ASSETS_DIR / "icons" / "vinqelo-logo.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    70,
                    70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        copy = QVBoxLayout()
        copy.setSpacing(3)
        brand = QLabel("Vinqelo Player")
        brand.setObjectName("loadingBannerBrand")
        caption = QLabel(translate_text("TU MÚSICA, A TU MANERA"))
        caption.setObjectName("loadingBannerCaption")
        self.message = QLabel(translate_text("Preparando el reproductor…"))
        self.message.setObjectName("loadingBannerMessage")
        self.message.setWordWrap(True)
        copy.addWidget(brand)
        copy.addWidget(caption)
        copy.addStretch(1)
        copy.addWidget(self.message)
        content.addWidget(logo)
        content.addLayout(copy, 1)
        panel_layout.addLayout(content)

        self.progress = QProgressBar()
        self.progress.setObjectName("loadingBannerProgress")
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(18)
        panel_layout.addWidget(self.progress)

        self.setStyleSheet(
            """
            QFrame#loadingBannerPanel {
                background-color: #0d1729;
                border: 1px solid #345b91;
                border-radius: 0;
            }
            QLabel#loadingBannerLogo {
                background-color: #101d33;
                border: 1px solid #2d4770;
                border-radius: 0;
            }
            QLabel#loadingBannerBrand {
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 21px;
                font-weight: 700;
            }
            QLabel#loadingBannerCaption {
                color: #6f9ce0;
                font-family: "Segoe UI";
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#loadingBannerMessage {
                color: #c8d8ed;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 600;
            }
            QProgressBar#loadingBannerProgress {
                background-color: #172743;
                border: none;
                border-radius: 0;
                color: #ffffff;
                font-family: "Segoe UI";
                font-size: 10px;
                font-weight: 700;
                text-align: center;
            }
            QProgressBar#loadingBannerProgress::chunk {
                background-color: #397fe2;
                border-radius: 0;
            }
            """
        )
        self._message_timer = QTimer(self)
        self._message_timer.setInterval(1050)
        self._message_timer.timeout.connect(self._next_message)
        self.hide()

    def start(self, messages: Sequence[str], *, determinate: bool = False) -> None:
        self._messages = [translate_text(message) for message in messages if message]
        self._message_index = 0
        if self._messages:
            self.message.setText(self._messages[0])
        if determinate:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setTextVisible(True)
        else:
            self.progress.setRange(0, 0)
            self.progress.setTextVisible(False)
        self.center_banner()
        self.show()
        self.raise_()
        self._message_timer.start()

    def show_message(self, message: str) -> None:
        self.message.setText(translate_text(message))
        self.center_banner()
        self.show()
        self.raise_()

    def set_progress(self, current: int, total: int, item_name: str = "") -> None:
        total = max(0, int(total))
        current = max(0, int(current))
        if total <= 0:
            self.progress.setRange(0, 0)
            self.progress.setTextVisible(False)
            return
        percent = max(0, min(100, round(current * 100 / total)))
        self.progress.setRange(0, 100)
        self.progress.setValue(percent)
        self.progress.setFormat(f"{percent}%")
        self.progress.setTextVisible(True)
        if item_name:
            self.message.setText(
                translate_text("Revisando biblioteca…") + f"  {item_name}"
            )

    def stop(self) -> None:
        self._message_timer.stop()
        self.hide()

    def center_banner(self) -> None:
        parent = self.parentWidget()
        if parent is not None and not self._startup:
            self.move(
                max(0, (parent.width() - self.width()) // 2),
                max(0, (parent.height() - self.height()) // 2),
            )
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        self.move(
            area.x() + (area.width() - self.width()) // 2,
            area.y() + (area.height() - self.height()) // 2,
        )

    def _next_message(self) -> None:
        if len(self._messages) < 2:
            return
        self._message_index = (self._message_index + 1) % len(self._messages)
        self.message.setText(self._messages[self._message_index])
