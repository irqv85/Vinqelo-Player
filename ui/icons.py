"""Iconos vectoriales dibujados con Qt para evitar símbolos de fuente."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def navigation_icon(kind: str, color: str = "#8fa7c7") -> QIcon:
    """Crea un icono lateral nítido y consistente con el tema."""
    size = 24
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "library":
        painter.drawRoundedRect(QRectF(4, 5, 4, 14), 1, 1)
        painter.drawRoundedRect(QRectF(10, 4, 4, 15), 1, 1)
        painter.drawRoundedRect(QRectF(16, 7, 4, 12), 1, 1)
        painter.drawLine(QPointF(3, 20), QPointF(21, 20))
    elif kind == "albums":
        painter.drawEllipse(QRectF(3.5, 3.5, 17, 17))
        painter.drawEllipse(QRectF(9, 9, 6, 6))
        painter.drawLine(QPointF(12, 4), QPointF(12, 8))
    elif kind == "artists":
        painter.drawEllipse(QRectF(8, 3, 8, 8))
        painter.drawArc(QRectF(4, 11, 16, 11), 0, 180 * 16)
    elif kind == "compilations":
        painter.drawEllipse(QRectF(3, 7, 12, 12))
        painter.drawEllipse(QRectF(9, 3, 12, 12))
        painter.drawEllipse(QRectF(7.5, 11.5, 3, 3))
        painter.drawEllipse(QRectF(13.5, 7.5, 3, 3))
    elif kind == "folders":
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(9, 7)
        path.lineTo(11, 9)
        path.lineTo(21, 9)
        path.lineTo(19, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(3, 7), QPointF(3, 19))
    elif kind == "folder_add":
        path = QPainterPath()
        path.moveTo(2, 7); path.lineTo(8, 7); path.lineTo(10, 9)
        path.lineTo(20, 9); path.lineTo(19, 18); path.lineTo(2, 18); path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(15, 11), QPointF(15, 16))
        painter.drawLine(QPointF(12.5, 13.5), QPointF(17.5, 13.5))
    elif kind == "file":
        path = QPainterPath()
        path.moveTo(6, 3); path.lineTo(14, 3); path.lineTo(19, 8)
        path.lineTo(19, 21); path.lineTo(6, 21); path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(14, 3), QPointF(14, 8))
        painter.drawLine(QPointF(14, 8), QPointF(19, 8))
        painter.drawEllipse(QRectF(9, 14, 3, 3))
        painter.drawLine(QPointF(12, 15.5), QPointF(12, 10.5))
        painter.drawLine(QPointF(12, 10.5), QPointF(16, 9.5))
    elif kind == "queue":
        for y in (6, 12, 18):
            painter.drawEllipse(QRectF(3, y - 1, 2, 2))
            painter.drawLine(QPointF(8, y), QPointF(20, y))
    elif kind == "now_playing":
        painter.drawLine(QPointF(5, 17), QPointF(5, 12))
        painter.drawLine(QPointF(10, 19), QPointF(10, 8))
        painter.drawLine(QPointF(15, 16), QPointF(15, 5))
        painter.drawLine(QPointF(20, 18), QPointF(20, 10))
    elif kind == "search":
        painter.drawEllipse(QRectF(4, 4, 11, 11))
        painter.drawLine(QPointF(14, 14), QPointF(20, 20))
    elif kind == "effects":
        painter.drawLine(QPointF(5, 5), QPointF(5, 19))
        painter.drawLine(QPointF(12, 5), QPointF(12, 19))
        painter.drawLine(QPointF(19, 5), QPointF(19, 19))
        painter.drawEllipse(QRectF(2.5, 8, 5, 5))
        painter.drawEllipse(QRectF(9.5, 13, 5, 5))
        painter.drawEllipse(QRectF(16.5, 6, 5, 5))
    else:
        painter.drawEllipse(QRectF(5, 5, 14, 14))

    painter.end()
    return QIcon(pixmap)


NAV_ICON_SIZE = QSize(18, 18)


def transport_icon(kind: str, color: str = "#e7edf7", size: int = 24) -> QIcon:
    """Iconos nítidos para los controles del reproductor."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 2.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(QColor(color))
    if kind == "play":
        path = QPainterPath(); path.moveTo(8, 5); path.lineTo(19, 12); path.lineTo(8, 19); path.closeSubpath(); painter.drawPath(path)
    elif kind == "pause":
        painter.drawRoundedRect(QRectF(7, 5, 3.5, 14), 1, 1); painter.drawRoundedRect(QRectF(14, 5, 3.5, 14), 1, 1)
    elif kind == "stop":
        painter.drawRoundedRect(QRectF(7, 7, 10, 10), 1.5, 1.5)
    elif kind == "previous":
        painter.drawLine(QPointF(6, 6), QPointF(6, 18)); path = QPainterPath(); path.moveTo(18, 6); path.lineTo(8, 12); path.lineTo(18, 18); path.closeSubpath(); painter.drawPath(path)
    elif kind == "next":
        painter.drawLine(QPointF(18, 6), QPointF(18, 18)); path = QPainterPath(); path.moveTo(6, 6); path.lineTo(16, 12); path.lineTo(6, 18); path.closeSubpath(); painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)
