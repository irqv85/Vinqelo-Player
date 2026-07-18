"""Barra lateral compacta para fuentes de música y reproducción."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from config import APP_VERSION, ASSETS_DIR
from ui.icons import NAV_ICON_SIZE, navigation_icon


class Sidebar(QFrame):
    section_selected = Signal(str)
    about_requested = Signal()

    LIBRARY_SECTIONS = (
        ("library", "Biblioteca", "library"),
        ("search", "Buscar", "search"),
        ("artists", "Artistas", "artists"),
        ("albums", "Álbumes", "albums"),
        ("compilations", "Compilaciones", "compilations"),
        ("folders", "Carpetas", "folders"),
        ("smart_playlists", "Smart Playlist", "queue"),
        ("playlists", "Listas de reproducción", "queue"),
    )
    PLAYBACK_SECTIONS = (
        ("now_playing", "Reproducción en curso", "now_playing"),
        ("queue", "Cola de reproducción", "queue"),
    )

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(226)
        self._buttons: dict[str, QPushButton] = {}
        self._icon_kinds: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(3)

        brand_block = QFrame()
        brand_block.setObjectName("brandBlock")
        brand_layout = QHBoxLayout(brand_block)
        brand_layout.setContentsMargins(10, 9, 10, 9)
        brand_layout.setSpacing(9)

        logo = QLabel()
        logo.setFixedSize(42, 42)
        logo_path = ASSETS_DIR / "icons" / "vinqelo-v.png"
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(
                    logo.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        brand_text = QWidget()
        brand_text_layout = QVBoxLayout(brand_text)
        brand_text_layout.setContentsMargins(0, 0, 0, 0)
        brand_text_layout.setSpacing(0)
        brand = QLabel("Vinqelo")
        brand.setObjectName("brandName")
        caption = QLabel("PLAYER LOCAL")
        caption.setObjectName("brandCaption")
        caption.setStyleSheet("font-size: 9px; letter-spacing: 1px;")
        brand_text_layout.addWidget(brand)
        brand_text_layout.addWidget(caption)

        brand_layout.addWidget(logo)
        brand_layout.addWidget(brand_text, 1)
        layout.addWidget(brand_block)

        self._add_group(layout, "TU MÚSICA", self.LIBRARY_SECTIONS)
        self._add_group(layout, "REPRODUCCIÓN", self.PLAYBACK_SECTIONS)

        layout.addStretch(1)
        about_button = QPushButton("Acerca de")
        about_button.setObjectName("aboutButton")
        about_button.setIcon(navigation_icon("info"))
        about_button.setIconSize(NAV_ICON_SIZE)
        about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        about_button.clicked.connect(self.about_requested.emit)
        layout.addWidget(about_button)
        version_label = QLabel(f"Vinqelo Player  ·  {APP_VERSION}")
        version_label.setObjectName("mutedLabel")
        version_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(version_label)

        self.select("library", emit_signal=False)
        self.set_now_playing_available(False)

    def _add_group(
        self,
        layout: QVBoxLayout,
        title: str,
        sections: tuple[tuple[str, str, str], ...],
    ) -> None:
        group_label = QLabel(title)
        group_label.setObjectName("navGroup")
        layout.addWidget(group_label)
        for key, label, icon_kind in sections:
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setIcon(navigation_icon(icon_kind))
            button.setIconSize(NAV_ICON_SIZE)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, section=key: self.select(section))
            layout.addWidget(button)
            self._buttons[key] = button
            self._icon_kinds[key] = icon_kind

    def set_player_available(self, available: bool) -> None:
        # El estado técnico del motor no se muestra en la navegación lateral.
        _ = available

    def set_now_playing_available(self, available: bool) -> None:
        button = self._buttons.get("now_playing")
        if button is not None:
            button.setEnabled(available)

    def is_selected(self, section: str) -> bool:
        button = self._buttons.get(section)
        return bool(button and button.property("active"))

    def select(self, section: str, *, emit_signal: bool = True) -> None:
        if section not in self._buttons:
            return
        for key, button in self._buttons.items():
            is_active = key == section
            button.setProperty("active", is_active)
            button.setIcon(
                navigation_icon(
                    self._icon_kinds[key],
                    "#4b9aff" if is_active else "#8fa7c7",
                )
            )
            button.style().unpolish(button)
            button.style().polish(button)
        if emit_signal:
            self.section_selected.emit(section)
