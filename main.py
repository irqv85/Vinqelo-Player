"""Punto de entrada de Vinqelo Player."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from config import APP_NAME, APP_VERSION, ASSETS_DIR, DATABASE_PATH
from single_instance import SingleInstanceCoordinator
from ui.loading_banner import LoadingBanner


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Vinqelo")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(ASSETS_DIR / "icons" / "vinqelo-v.png")))
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    from library.audio_formats import is_supported_audio

    launch_files = [
        path
        for argument in sys.argv[1:]
        if is_supported_audio(path := Path(argument))
    ]
    instance = SingleInstanceCoordinator(parent=app)
    if not instance.start_or_forward(launch_files):
        return 0
    app._vinqelo_single_instance = instance
    app.aboutToQuit.connect(instance.close)

    from ui.scrolling import enable_smooth_scrolling

    scroll_tuner = enable_smooth_scrolling(app)
    app._vinqelo_scroll_tuner = scroll_tuner
    startup_preferences = QSettings("Vinqelo", "Vinqelo Player")
    from ui.i18n import detect_system_language, enable_translation

    if startup_preferences.contains("interface/language"):
        startup_language = str(
            startup_preferences.value("interface/language", "es")
        )
    else:
        startup_language = detect_system_language()
        startup_preferences.setValue("interface/language", startup_language)

    translation_manager = enable_translation(
        app, startup_language
    )
    app._vinqelo_translation_manager = translation_manager
    startup = LoadingBanner(startup=True)
    startup.start(
        [
            "Preparando el reproductor…",
            "Organizando tu música…",
            "Casi listo…",
        ]
    )
    app.processEvents()
    # El splash nativo de PyInstaller cubre la extracción inicial. En cuanto
    # el banner Qt está visible debe cerrarse para no tapar la ventana real.
    try:
        import pyi_splash

        pyi_splash.close()
    except ImportError:
        pass
    logger = logging.getLogger(__name__)

    try:
        from logging_config import configure_logging

        configure_logging()
        startup.show_message("Organizando tu música…")
        app.processEvents()
        from database.manager import DatabaseManager

        database = DatabaseManager(DATABASE_PATH)
        database.initialize()
        startup.show_message("Casi listo…")
        app.processEvents()
        from ui.main_window import MainWindow
        from ui.styles import build_stylesheet
        preferences = QSettings("Vinqelo", "Vinqelo Player")
        app.setStyleSheet(
            build_stylesheet(
                str(preferences.value("appearance/theme", "vinqelo")),
                preferences.value("appearance/font_size", 13, type=int),
            )
        )
        window = MainWindow(
            database, confirm_initial_library=not bool(launch_files)
        )
        window.show()
        if launch_files:
            window.open_audio_paths(launch_files)
        instance.set_activation_handler(window.handle_external_activation)
        startup.stop()
        logger.info("Vinqelo Player iniciado")
        return app.exec()
    except Exception as exc:  # Protege el arranque y deja el detalle en el log.
        startup.stop()
        logger.exception("No se pudo iniciar Vinqelo Player")
        QMessageBox.critical(
            None,
            "No se pudo iniciar Vinqelo Player",
            "Ocurrio un error al iniciar la aplicacion. "
            "Revise logs/vinqelo_player.log para obtener mas detalles.\n\n"
            f"Detalle: {exc}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
