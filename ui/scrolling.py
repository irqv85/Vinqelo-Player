"""Desplazamiento general suave y liviano para la interfaz."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QAbstractItemView, QAbstractScrollArea


class ScrollTuner(QObject):
    """Configura cada área al mostrarse, sin animaciones ni temporizadores."""

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if (
            event.type() in (QEvent.Type.Polish, QEvent.Type.Show)
            and isinstance(watched, QAbstractScrollArea)
            and not watched.property("vinqeloSmoothScroll")
        ):
            watched.setProperty("vinqeloSmoothScroll", True)
            if isinstance(watched, QAbstractItemView):
                watched.setVerticalScrollMode(
                    QAbstractItemView.ScrollMode.ScrollPerPixel
                )
                watched.setHorizontalScrollMode(
                    QAbstractItemView.ScrollMode.ScrollPerPixel
                )
            # Qt calcula algunos pasos al mostrar la vista. Se ajustan una sola
            # vez justo después; no hay animación ni temporizador permanente.
            QTimer.singleShot(0, lambda area=watched: self._set_small_steps(area))
        return super().eventFilter(watched, event)

    @staticmethod
    def _set_small_steps(area: QAbstractScrollArea) -> None:
        try:
            area.verticalScrollBar().setSingleStep(24)
            area.horizontalScrollBar().setSingleStep(24)
        except RuntimeError:
            pass


def enable_smooth_scrolling(application: object) -> ScrollTuner:
    """Reduce a una línea cada paso de rueda y configura vistas dinámicas."""
    application.styleHints().setWheelScrollLines(1)
    tuner = ScrollTuner(application)
    application.installEventFilter(tuner)
    return tuner
