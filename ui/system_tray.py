"""Integración discreta de Vinqelo con la bandeja del sistema."""

from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMainWindow, QMenu, QSystemTrayIcon

from config import APP_NAME, ASSETS_DIR
from ui.i18n import translate_text
from ui.icons import transport_icon


class ExportProgress(Protocol):
    def restore_from_tray(self) -> None: ...

    def request_cancel(self) -> None: ...


def progress_percent(current: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round(current * 100 / total)))


class VinqeloSystemTray(QObject):
    """Mantiene reproducción y exportaciones accesibles al ocultar la ventana."""

    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self.window = window
        self._base_pixmap = QPixmap(
            str(ASSETS_DIR / "icons" / "vinqelo-v.png")
        )
        self._title = ""
        self._artist = ""
        self._state = "stopped"
        self._icon_color = "#e7edf7"
        self._export: ExportProgress | None = None
        self._export_current = 0
        self._export_total = 0
        self._export_detail = ""

        self.icon = QSystemTrayIcon(self._plain_icon(), self)
        self.menu = QMenu(window)

        self.track_action = QAction(APP_NAME, self.menu)
        self.track_action.setEnabled(False)
        self.show_action = QAction(self.menu)
        self.previous_action = QAction(
            transport_icon("previous"), "", self.menu
        )
        self.play_action = QAction(transport_icon("play"), "", self.menu)
        self.stop_action = QAction(transport_icon("stop"), "", self.menu)
        self.next_action = QAction(transport_icon("next"), "", self.menu)
        self.export_status_action = QAction(self.menu)
        self.export_status_action.setEnabled(False)
        self.export_show_action = QAction(self.menu)
        self.export_cancel_action = QAction(self.menu)
        self.quit_action = QAction(self.menu)

        self.menu.addAction(self.track_action)
        self.menu.addSeparator()
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.previous_action)
        self.menu.addAction(self.play_action)
        self.menu.addAction(self.stop_action)
        self.menu.addAction(self.next_action)
        self.playback_separator = self.menu.addSeparator()
        self.menu.addAction(self.export_status_action)
        self.menu.addAction(self.export_show_action)
        self.menu.addAction(self.export_cancel_action)
        self.export_separator = self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.show_action.triggered.connect(self.restore_window)
        self.previous_action.triggered.connect(
            lambda: self.window._run_media_action("previous")
        )
        self.play_action.triggered.connect(
            lambda: self.window._run_media_action("play_pause")
        )
        self.stop_action.triggered.connect(
            lambda: self.window._run_media_action("stop")
        )
        self.next_action.triggered.connect(
            lambda: self.window._run_media_action("next")
        )
        self.export_show_action.triggered.connect(self._show_export)
        self.export_cancel_action.triggered.connect(self._cancel_export)
        self.quit_action.triggered.connect(self.window._quit_application)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._activated)

        self._set_export_actions_visible(False)
        self.apply_theme(str(getattr(window, "_active_theme", "vinqelo")))
        self.retranslate()
        self._update_tooltip()
        if self.is_available:
            self.icon.show()

    @property
    def is_available(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def bind_player(self, controller: QObject | None) -> None:
        enabled = controller is not None
        for action in (
            self.previous_action,
            self.play_action,
            self.stop_action,
            self.next_action,
        ):
            action.setEnabled(enabled)
        if controller is None:
            return
        controller.track_changed.connect(self.set_track)
        controller.state_changed.connect(self.set_playback_state)

    def retranslate(self) -> None:
        self.show_action.setText(translate_text("Mostrar Vinqelo"))
        self.previous_action.setText(translate_text("Anterior"))
        self.stop_action.setText(translate_text("Detener"))
        self.next_action.setText(translate_text("Siguiente"))
        self.export_show_action.setText(translate_text("Mostrar progreso"))
        self.export_cancel_action.setText(
            translate_text("Cancelar exportación")
        )
        self.quit_action.setText(translate_text("Salir de Vinqelo"))
        self._update_play_action()
        self._update_export_status()
        self._update_tooltip()

    def apply_theme(self, theme: str) -> None:
        self._icon_color = (
            "#40576d" if theme == "musicmatch" else "#e7edf7"
        )
        self.previous_action.setIcon(
            transport_icon("previous", self._icon_color)
        )
        self.stop_action.setIcon(
            transport_icon("stop", self._icon_color)
        )
        self.next_action.setIcon(
            transport_icon("next", self._icon_color)
        )
        self._update_play_action()

    def set_track(self, title: str, artist: str, _file_path: str) -> None:
        self._title = title.strip()
        self._artist = artist.strip()
        display = self._title or APP_NAME
        if self._artist:
            display = f"{display} — {self._artist}"
        self.track_action.setText(display)
        self._update_tooltip()

    def set_playback_state(self, state: str) -> None:
        self._state = state
        self._update_play_action()
        self._update_tooltip()

    def restore_window(self) -> None:
        if self.window.isMinimized():
            self.window.showNormal()
        else:
            self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def notify_running_in_background(self) -> None:
        self.icon.showMessage(
            APP_NAME,
            translate_text(
                "Vinqelo seguirá disponible aquí mientras reproduce música."
            ),
            QSystemTrayIcon.MessageIcon.Information,
            4500,
        )

    def begin_export(
        self,
        progress: ExportProgress,
        current: int,
        total: int,
        detail: str,
    ) -> None:
        self._export = progress
        self._export_current = current
        self._export_total = total
        self._export_detail = detail
        self._set_export_actions_visible(True)
        self._update_export_status()
        self._update_tooltip()
        self.icon.setIcon(self._progress_icon())
        if self.is_available:
            self.icon.show()

    def update_export(
        self,
        progress: ExportProgress,
        current: int,
        total: int,
        detail: str,
    ) -> None:
        if progress is not self._export:
            return
        self._export_current = current
        self._export_total = total
        self._export_detail = detail
        self._update_export_status()
        self._update_tooltip()
        self.icon.setIcon(self._progress_icon())

    def finish_export(
        self,
        progress: ExportProgress,
        title: str,
        message: str,
        *,
        success: bool,
        notify: bool,
    ) -> None:
        if progress is self._export:
            self._export = None
            self._export_current = 0
            self._export_total = 0
            self._export_detail = ""
            self._set_export_actions_visible(False)
            self.icon.setIcon(self._plain_icon())
            self._update_tooltip()
        if notify and self.is_available:
            message_icon = (
                QSystemTrayIcon.MessageIcon.Information
                if success
                else QSystemTrayIcon.MessageIcon.Warning
            )
            self.icon.showMessage(title, message, message_icon, 8000)

    def _update_play_action(self) -> None:
        playing = self._state == "playing"
        self.play_action.setText(
            translate_text("Pausar" if playing else "Reproducir")
        )
        self.play_action.setIcon(
            transport_icon(
                "pause" if playing else "play", self._icon_color
            )
        )

    def _update_export_status(self) -> None:
        percent = progress_percent(
            self._export_current, self._export_total
        )
        self.export_status_action.setText(
            f"{translate_text('Exportación en curso')} · {percent}%"
        )

    def _update_tooltip(self) -> None:
        lines = [APP_NAME]
        if self._title:
            current = self._title
            if self._artist:
                current += f" — {self._artist}"
            lines.append(current[:100])
        if self._export is not None:
            percent = progress_percent(
                self._export_current, self._export_total
            )
            lines.append(
                f"{translate_text('Exportación en curso')} · {percent}%"
            )
            detail = self._export_detail.replace("\n", " · ").strip()
            if detail:
                lines.append(detail[:100])
        self.icon.setToolTip("\n".join(lines)[:240])

    def _plain_icon(self) -> QIcon:
        return QIcon(self._base_pixmap)

    def _progress_icon(self) -> QIcon:
        canvas = QPixmap(64, 64)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._base_pixmap.isNull():
            painter.drawPixmap(
                3,
                1,
                self._base_pixmap.scaled(
                    58,
                    58,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ),
            )
        percent = progress_percent(
            self._export_current, self._export_total
        )
        painter.fillRect(2, 59, 60, 3, QColor(37, 68, 112, 210))
        painter.fillRect(
            2,
            59,
            round(60 * percent / 100),
            3,
            QColor("#4b9aff"),
        )
        painter.end()
        return QIcon(canvas)

    def _set_export_actions_visible(self, visible: bool) -> None:
        self.export_status_action.setVisible(visible)
        self.export_show_action.setVisible(visible)
        self.export_cancel_action.setVisible(visible)
        self.export_separator.setVisible(visible)

    def _show_export(self) -> None:
        if self._export is not None:
            self._export.restore_from_tray()

    def _cancel_export(self) -> None:
        if self._export is not None:
            self._export.request_cancel()

    def _activated(
        self, reason: QSystemTrayIcon.ActivationReason
    ) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.restore_window()
