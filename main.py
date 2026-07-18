"""Punto de entrada de Vinqelo Player."""

from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from config import APP_NAME, APP_VERSION, ASSETS_DIR, DATABASE_PATH
from ui.loading_banner import LoadingBanner


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Vinqelo")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(ASSETS_DIR / "icons" / "vinqelo-v.png")))
    app.setStyle("Fusion")
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
        from ui.styles import APP_STYLESHEET

        app.setStyleSheet(APP_STYLESHEET)
        window = MainWindow(database)
        window.show()
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
