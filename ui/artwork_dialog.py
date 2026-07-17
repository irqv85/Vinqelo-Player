"""Selector y vista previa reutilizable para imágenes manuales."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)


class ArtworkPreviewDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        pixmap: QPixmap,
        *,
        selectable: bool,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("artworkPreviewDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(440, 500)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image = QLabel()
        image.setObjectName("artworkPreview")
        image.setFixedSize(390, 390)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image.setPixmap(
            pixmap.scaled(
                image.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        layout.addWidget(heading)
        layout.addWidget(image, 1, Qt.AlignmentFlag.AlignCenter)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
            if selectable
            else QDialogButtonBox.StandardButton.Close
        )
        if selectable:
            buttons.button(QDialogButtonBox.StandardButton.Save).setText("Usar esta imagen")
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
        else:
            buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def choose_artwork(parent: QWidget, title: str) -> Path | None:
    selected, _filter = QFileDialog.getOpenFileName(
        parent,
        title,
        str(Path.home() / "Pictures"),
        "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp);;Todos los archivos (*)",
    )
    if not selected:
        return None
    pixmap = QPixmap(selected)
    if pixmap.isNull():
        QMessageBox.warning(parent, "Imagen no válida", "No se pudo abrir la imagen seleccionada.")
        return None
    dialog = ArtworkPreviewDialog(parent, title, pixmap, selectable=True)
    return Path(selected) if dialog.exec() == QDialog.DialogCode.Accepted else None


def show_artwork(parent: QWidget, title: str, pixmap: QPixmap) -> None:
    if pixmap.isNull():
        QMessageBox.information(parent, title, "No hay una imagen disponible.")
        return
    ArtworkPreviewDialog(parent, title, pixmap, selectable=False).exec()
