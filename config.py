"""Configuracion compartida de Vinqelo Player."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Vinqelo Player"
APP_VERSION = "0.7.2"
APP_AUTHOR = "Irán Quintero"
APP_AUTHOR_EMAIL = "vinqeloapp@gmail.com"
APP_LICENSE = "GNU General Public License v3.0"
STORE_PACKAGE_FAMILY_NAME = "irqv8.VinqeloPlayer_4mh58ts6mv4gw"
PROJECT_ROOT = Path(__file__).resolve().parent


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _runtime_root() -> Path:
    custom_root = os.environ.get("VINQELO_DATA_DIR")
    if custom_root:
        return Path(custom_root).expanduser().resolve()

    if os.environ.get("VINQELO_STORE_BUILD") == "1":
        # Un paquete MSIX se instala en una ubicacion de solo lectura. Los datos
        # duraderos de la biblioteca viven en LocalState, como espera Windows.
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        return (
            local_app_data
            / "Packages"
            / STORE_PACKAGE_FAMILY_NAME
            / "LocalState"
        )

    if _is_frozen():
        # La edición empaquetada es portable: conserva biblioteca, carátulas y
        # logs junto al ejecutable, sin escribir dentro del paquete temporal.
        return Path(sys.executable).resolve().parent / f"{APP_NAME} Data"

    return PROJECT_ROOT


RUNTIME_ROOT = _runtime_root()
ASSETS_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "assets"
LICENSE_PATH = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "LICENSE"
DATABASE_PATH = (
    RUNTIME_ROOT / "library.sqlite3"
    if _is_frozen() or os.environ.get("VINQELO_DATA_DIR")
    else PROJECT_ROOT / "database" / "library.sqlite3"
)
LOG_DIR = RUNTIME_ROOT / "logs"
LOG_PATH = LOG_DIR / "vinqelo_player.log"
COVER_CACHE_DIR = RUNTIME_ROOT / "cover_cache"
