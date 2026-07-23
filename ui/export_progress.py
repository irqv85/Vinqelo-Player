"""Progreso de exportación minimizable a la bandeja de Windows."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.i18n import translate_text


class ExportProgressDialog(QDialog):
    """Muestra el avance y continúa discretamente desde la bandeja."""

    canceled = Signal()

    def __init__(
        self,
        label_text: str,
        cancel_text: str,
        minimum: int,
        maximum: int,
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("exportProgressDialog")
        self.setModal(False)
        self.setMinimumWidth(500)
        self._active = True
        self._minimized_to_tray = False
        self._current = minimum
        self._total = maximum
        self._detail = label_text
        self._tray = self._find_application_tray(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)
        self.detail_label = QLabel(label_text)
        self.detail_label.setObjectName("exportProgressDetail")
        self.detail_label.setWordWrap(True)
        layout.addWidget(self.detail_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(minimum, maximum)
        self.progress_bar.setValue(minimum)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        self.count_label = QLabel(
            translate_text(f"{minimum} de {maximum} pistas")
        )
        self.count_label.setObjectName("mutedLabel")
        layout.addWidget(self.count_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.minimize_button = QPushButton(
            translate_text("Minimizar a la bandeja")
        )
        self.minimize_button.setObjectName("secondaryButton")
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.setObjectName("primaryButton")
        self.minimize_button.clicked.connect(self.minimize_to_tray)
        self.cancel_button.clicked.connect(self._request_cancel)
        buttons.addWidget(self.minimize_button)
        buttons.addWidget(self.cancel_button)
        layout.addLayout(buttons)

        self.minimize_button.setEnabled(
            bool(self._tray and self._tray.is_available)
        )
        if self._tray is not None:
            self._tray.begin_export(
                self, self._current, self._total, self._detail
            )

    @property
    def is_minimized_to_tray(self) -> bool:
        return self._minimized_to_tray

    def setAutoClose(self, _enabled: bool) -> None:  # noqa: N802 - API compatible
        pass

    def setMinimumDuration(self, _milliseconds: int) -> None:  # noqa: N802
        pass

    def setMaximum(self, maximum: int) -> None:  # noqa: N802
        self._total = maximum
        self.progress_bar.setMaximum(maximum)
        self._refresh_count()

    def setValue(self, value: int) -> None:  # noqa: N802
        self._current = value
        self.progress_bar.setValue(value)
        self._refresh_count()
        self._update_tray()

    def setLabelText(self, text: str) -> None:  # noqa: N802
        self._detail = text
        self.detail_label.setText(text)
        self._update_tray()

    def minimize_to_tray(self) -> None:
        if self._tray is None or not self._tray.is_available:
            return
        self._minimized_to_tray = True
        self._update_tray()
        self.hide()

    def restore_from_tray(self) -> None:
        if not self._active:
            return
        self._minimized_to_tray = False
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def finish(
        self,
        title: str,
        message: str,
        *,
        success: bool = True,
    ) -> bool:
        """Cierra el progreso y notifica sin robar foco si estaba minimizado."""
        minimized = self._minimized_to_tray
        self._active = False
        self.hide()
        if self._tray is not None:
            self._tray.finish_export(
                self,
                title,
                message,
                success=success,
                notify=minimized,
            )
        self.deleteLater()
        return minimized

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._active and self._tray is not None and self._tray.is_available:
            event.ignore()
            self.minimize_to_tray()
            return
        super().closeEvent(event)

    def request_cancel(self) -> None:
        self._request_cancel()

    def _request_cancel(self) -> None:
        if not self._active or not self.cancel_button.isEnabled():
            return
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText(translate_text("Cancelando…"))
        self.canceled.emit()

    def _refresh_count(self) -> None:
        self.count_label.setText(
            translate_text(f"{self._current} de {self._total} pistas")
        )

    def _update_tray(self) -> None:
        if self._tray is not None:
            self._tray.update_export(
                self, self._current, self._total, self._detail
            )

    @staticmethod
    def _find_application_tray(parent: QWidget) -> object | None:
        window = parent.window()
        return getattr(window, "_system_tray", None)
