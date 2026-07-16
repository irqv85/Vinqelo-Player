"""Punto de entrada de Vinqelo Player."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from config import APP_NAME, APP_VERSION, DATABASE_PATH
from database.manager import DatabaseManager
from logging_config import configure_logging
from ui.main_window import MainWindow
from ui.styles import APP_STYLESHEET


def main() -> int:
    configure_logging()
    logger = logging.getLogger(__name__)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    try:
        database = DatabaseManager(DATABASE_PATH)
        database.initialize()
        window = MainWindow(database)
        window.show()
        logger.info("Vinqelo Player iniciado")
        return app.exec()
    except Exception as exc:  # Protege el arranque y deja el detalle en el log.
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

