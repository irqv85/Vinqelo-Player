"""Preferencias generales de Vinqelo Player."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget,
)

THEMES = {
    "vinqelo": "Vinqelo · Azul", "clementine": "Clementine · Naranja",
    "amarok": "Amarok · Morado", "emerald": "Esmeralda", "graphite": "Grafito",
    "musicmatch": "MusicMatch clásico · Gris azulado",
}
LANGUAGES = {
    "es": "Español", "en": "English", "pt": "Português",
    "fr": "Français", "de": "Deutsch", "it": "Italiano",
}


class SettingsDialog(QDialog):
    settings_applied = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = QSettings("Vinqelo", "Vinqelo Player")
        self.setWindowTitle("Configuración")
        self.setModal(True)
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        title = QLabel("Configuración")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        tabs = QTabWidget()
        tabs.setObjectName("settingsTabs")
        tabs.addTab(self._appearance_tab(), "Apariencia")
        tabs.addTab(self._language_tab(), "Idioma")
        tabs.addTab(self._privacy_tab(), "Privacidad")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _appearance_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(14, 16, 14, 16)
        self.theme = QComboBox()
        for key, label in THEMES.items():
            self.theme.addItem(label, key)
        current = str(self.settings.value("appearance/theme", "vinqelo"))
        self.theme.setCurrentIndex(max(0, self.theme.findData(current)))
        self.font_size = QSpinBox()
        self.font_size.setRange(11, 17)
        self.font_size.setSuffix(" px")
        self.font_size.setValue(self.settings.value("appearance/font_size", 13, type=int))
        self.show_menu_bar = QCheckBox("Mostrar barra de menú clásica")
        self.show_menu_bar.setChecked(
            self.settings.value("appearance/show_menu_bar", False, type=bool)
        )
        form.addRow("Estilo:", self.theme)
        form.addRow("Tamaño de la tipografía:", self.font_size)
        form.addRow("", self.show_menu_bar)
        return page

    def _language_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(14, 16, 14, 16)
        self.language = QComboBox()
        for key, label in LANGUAGES.items():
            self.language.addItem(label, key)
        current = str(self.settings.value("interface/language", "es"))
        self.language.setCurrentIndex(max(0, self.language.findData(current)))
        form.addRow("Idioma de la interfaz:", self.language)
        return page

    def _privacy_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 16, 14, 16)
        self.offline_mode = QCheckBox(
            "No descargar información de internet (modo local)"
        )
        self.offline_mode.setChecked(
            self.settings.value("privacy/offline_mode", False, type=bool)
        )
        note = QLabel(
            "Usa portadas de las carpetas, imágenes elegidas manualmente "
            "y metadatos de los archivos."
        )
        note.setObjectName("mutedLabel")
        note.setWordWrap(True)
        layout.addWidget(self.offline_mode)
        layout.addWidget(note)
        layout.addStretch(1)
        return page

    def _save(self) -> None:
        values = {
            "theme": self.theme.currentData(), "font_size": self.font_size.value(),
            "language": self.language.currentData(),
            "offline_mode": self.offline_mode.isChecked(),
            "show_menu_bar": self.show_menu_bar.isChecked(),
        }
        for key, value in (
            ("appearance/theme", values["theme"]),
            ("appearance/font_size", values["font_size"]),
            ("interface/language", values["language"]),
            ("privacy/offline_mode", values["offline_mode"]),
            ("appearance/show_menu_bar", values["show_menu_bar"]),
        ):
            self.settings.setValue(key, value)
        self.settings.sync()
        self.settings_applied.emit(values)
        self.accept()
