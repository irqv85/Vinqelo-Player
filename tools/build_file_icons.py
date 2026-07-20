"""Genera iconos de asociación de audio con la identidad de Vinqelo."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "icons" / "files"
FORMATS = ("MP3", "FLAC", "WAV", "OGG", "M4A", "AAC")
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
FONT_FAMILY = "Segoe UI"


def render(format_name: str) -> QImage:
    image = QImage(512, 512, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    document = QPainterPath()
    document.moveTo(82, 28)
    document.lineTo(340, 28)
    document.lineTo(430, 118)
    document.lineTo(430, 480)
    document.lineTo(82, 480)
    document.closeSubpath()
    body = QLinearGradient(82, 28, 430, 480)
    body.setColorAt(0, QColor("#162846"))
    body.setColorAt(1, QColor("#091427"))
    painter.setPen(QPen(QColor("#438df5"), 8))
    painter.setBrush(body)
    painter.drawPath(document)

    fold = QPainterPath()
    fold.moveTo(340, 28)
    fold.lineTo(340, 118)
    fold.lineTo(430, 118)
    fold.closeSubpath()
    fold_gradient = QLinearGradient(340, 28, 430, 118)
    fold_gradient.setColorAt(0, QColor("#7c3aed"))
    fold_gradient.setColorAt(1, QColor("#3b82f6"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(fold_gradient)
    painter.drawPath(fold)

    # V principal y pequeña onda, compartidas con la identidad del reproductor.
    v_font = QFont(FONT_FAMILY, 176, QFont.Weight.Black)
    painter.setFont(v_font)
    painter.setPen(QColor("#2f82ff"))
    painter.drawText(QRectF(105, 105, 300, 225), Qt.AlignmentFlag.AlignCenter, "V")
    wave_pen = QPen(QColor("#a78bfa"), 8)
    wave_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(wave_pen)
    points = [
        QPointF(138, 333), QPointF(174, 306), QPointF(210, 350),
        QPointF(250, 292), QPointF(292, 344), QPointF(336, 312),
        QPointF(374, 333),
    ]
    for start, end in zip(points, points[1:]):
        painter.drawLine(start, end)

    badge = QLinearGradient(82, 386, 430, 470)
    badge.setColorAt(0, QColor("#1f6feb"))
    badge.setColorAt(1, QColor("#6d28d9"))
    painter.setBrush(badge)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(QRectF(82, 386, 348, 94))
    label_font = QFont(FONT_FAMILY, 54, QFont.Weight.Bold)
    painter.setFont(label_font)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(
        QRectF(90, 388, 332, 86), Qt.AlignmentFlag.AlignCenter, format_name
    )
    painter.end()
    return image


def main() -> None:
    global FONT_FAMILY
    QApplication.instance() or QApplication([])
    font_id = QFontDatabase.addApplicationFont(
        str(Path("C:/Windows/Fonts/segoeuib.ttf"))
    )
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        FONT_FAMILY = families[0]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for format_name in FORMATS:
        source = OUTPUT / f"vinqelo-{format_name.lower()}.png"
        render(format_name).save(str(source), "PNG")
        with Image.open(source) as image:
            image.save(
                OUTPUT / f"vinqelo-{format_name.lower()}.ico",
                format="ICO",
                sizes=[(size, size) for size in ICON_SIZES],
            )


if __name__ == "__main__":
    main()
