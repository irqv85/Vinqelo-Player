"""Iconos vectoriales dibujados con Qt para evitar símbolos de fuente."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap


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
    elif kind == "refresh":
        painter.drawArc(QRectF(4.5, 4.5, 15, 15), 35 * 16, 125 * 16)
        painter.drawArc(QRectF(4.5, 4.5, 15, 15), 215 * 16, 125 * 16)
        upper = QPainterPath()
        upper.moveTo(18.5, 4.8)
        upper.lineTo(19.2, 8.8)
        upper.lineTo(15.2, 8.1)
        painter.drawPath(upper)
        lower = QPainterPath()
        lower.moveTo(5.5, 19.2)
        lower.lineTo(4.8, 15.2)
        lower.lineTo(8.8, 15.9)
        painter.drawPath(lower)
    elif kind == "export":
        painter.drawLine(QPointF(12, 4), QPointF(12, 14))
        painter.drawLine(QPointF(8.5, 10.5), QPointF(12, 14))
        painter.drawLine(QPointF(15.5, 10.5), QPointF(12, 14))
        tray = QPainterPath()
        tray.moveTo(5, 15)
        tray.lineTo(5, 20)
        tray.lineTo(19, 20)
        tray.lineTo(19, 15)
        painter.drawPath(tray)
    elif kind == "effects":
        painter.drawLine(QPointF(5, 5), QPointF(5, 19))
        painter.drawLine(QPointF(12, 5), QPointF(12, 19))
        painter.drawLine(QPointF(19, 5), QPointF(19, 19))
        painter.drawEllipse(QRectF(2.5, 8, 5, 5))
        painter.drawEllipse(QRectF(9.5, 13, 5, 5))
        painter.drawEllipse(QRectF(16.5, 6, 5, 5))
    elif kind == "info":
        painter.drawEllipse(QRectF(4, 4, 16, 16))
        painter.drawLine(QPointF(12, 10.5), QPointF(12, 17))
        painter.drawPoint(QPointF(12, 7.5))
    elif kind == "settings":
        font = QFont("Segoe MDL2 Assets")
        font.setPixelSize(16)
        painter.setFont(font)
        painter.setPen(QColor(color))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawText(
            QRectF(0, 0, size, size),
            Qt.AlignmentFlag.AlignCenter,
            "\ue713",  # Icono oficial de Configuración de Windows.
        )
    else:
        painter.drawEllipse(QRectF(5, 5, 14, 14))

    painter.end()
    return QIcon(pixmap)


def library_folder_icon(accent: str = "#438df5", size: int = 64) -> QIcon:
    """Carpeta musical acorde a las tarjetas oscuras de Vinqelo."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    scale = size / 64.0
    painter.scale(scale, scale)
    accent_color = QColor(accent)
    back_color = accent_color.darker(235)
    front_color = accent_color.darker(175)

    back = QPainterPath()
    back.moveTo(7, 17)
    back.lineTo(24, 17)
    back.cubicTo(26, 17, 28, 18, 30, 21)
    back.lineTo(34, 24)
    back.lineTo(57, 24)
    back.lineTo(57, 51)
    back.lineTo(7, 51)
    back.closeSubpath()
    painter.setPen(QPen(accent_color.darker(125), 1.5))
    painter.setBrush(back_color)
    painter.drawPath(back)

    front = QPainterPath()
    front.moveTo(6, 27)
    front.quadTo(6, 24, 10, 24)
    front.lineTo(58, 24)
    front.lineTo(52, 53)
    front.quadTo(51, 56, 47, 56)
    front.lineTo(10, 56)
    front.quadTo(6, 55, 6, 51)
    front.closeSubpath()
    painter.setPen(QPen(accent_color, 1.7))
    painter.setBrush(front_color)
    painter.drawPath(front)

    # Nota musical sencilla que identifica estas carpetas como música.
    painter.setPen(QPen(QColor("#e8f1ff"), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.setBrush(QColor("#e8f1ff"))
    painter.drawLine(QPointF(36, 34), QPointF(36, 47))
    painter.drawLine(QPointF(36, 34), QPointF(45, 32))
    painter.drawLine(QPointF(45, 32), QPointF(45, 44))
    painter.drawEllipse(QRectF(30, 44, 7, 5))
    painter.drawEllipse(QRectF(39, 41, 7, 5))
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
    elif kind in {"repeat_one", "repeat_all", "repeat_album", "repeat_artist"}:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(4, 6, 16, 11), 25 * 16, 145 * 16)
        painter.drawArc(QRectF(4, 7, 16, 11), 205 * 16, 145 * 16)
        painter.drawLine(QPointF(18, 5), QPointF(20, 8))
        painter.drawLine(QPointF(20, 8), QPointF(16.5, 8))
        painter.drawLine(QPointF(6, 19), QPointF(4, 16))
        painter.drawLine(QPointF(4, 16), QPointF(7.5, 16))
        if kind == "repeat_one":
            painter.drawText(QRectF(8, 7, 8, 10), Qt.AlignmentFlag.AlignCenter, "1")
        elif kind in {"repeat_album", "repeat_artist"}:
            painter.drawText(
                QRectF(7, 7, 10, 10), Qt.AlignmentFlag.AlignCenter,
                "D" if kind == "repeat_album" else "A",
            )
    elif kind.startswith("shuffle"):
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(4, 7), QPointF(8, 7))
        painter.drawLine(QPointF(8, 7), QPointF(16, 17))
        painter.drawLine(QPointF(16, 17), QPointF(20, 17))
        painter.drawLine(QPointF(17, 14), QPointF(20, 17))
        painter.drawLine(QPointF(20, 17), QPointF(17, 20))
        painter.drawLine(QPointF(4, 17), QPointF(8, 17))
        painter.drawLine(QPointF(8, 17), QPointF(16, 7))
        painter.drawLine(QPointF(16, 7), QPointF(20, 7))
        painter.drawLine(QPointF(17, 4), QPointF(20, 7))
        painter.drawLine(QPointF(20, 7), QPointF(17, 10))
        if kind != "shuffle":
            badge = {"shuffle_album": "D", "shuffle_artist": "A", "shuffle_global": "G"}.get(kind, "")
            painter.setBrush(QColor("#10192b"))
            painter.drawEllipse(QRectF(12, 11, 10, 10))
            painter.drawText(QRectF(12, 11, 10, 10), Qt.AlignmentFlag.AlignCenter, badge)
    painter.end()
    return QIcon(pixmap)


def window_control_icon(kind: str, color: str = "#dce8f8", size: int = 20) -> QIcon:
    """Iconos de ventana con el mismo trazo que los controles de transporte."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.7)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if kind == "minimize":
        painter.drawLine(QPointF(5, 14), QPointF(15, 14))
    elif kind == "maximize":
        painter.drawRect(QRectF(5.5, 5.5, 9, 9))
    elif kind == "restore":
        painter.drawRect(QRectF(4.5, 7.5, 8, 8))
        painter.drawLine(QPointF(7.5, 7), QPointF(7.5, 4.5))
        painter.drawLine(QPointF(7.5, 4.5), QPointF(15.5, 4.5))
        painter.drawLine(QPointF(15.5, 4.5), QPointF(15.5, 12.5))
        painter.drawLine(QPointF(15, 12.5), QPointF(12.8, 12.5))
    elif kind == "close":
        painter.drawLine(QPointF(6, 6), QPointF(14, 14))
        painter.drawLine(QPointF(14, 6), QPointF(6, 14))

    painter.end()
    return QIcon(pixmap)
