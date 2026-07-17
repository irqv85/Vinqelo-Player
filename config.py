"""Configuracion compartida de Vinqelo Player."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Vinqelo Player"
APP_VERSION = "0.7.0"
PROJECT_ROOT = Path(__file__).resolve().parent


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _runtime_root() -> Path:
    custom_root = os.environ.get("VINQELO_DATA_DIR")
    if custom_root:
        return Path(custom_root).expanduser().resolve()

    if _is_frozen():
        # La edición empaquetada es portable: conserva biblioteca, carátulas y
        # logs junto al ejecutable, sin escribir dentro del paquete temporal.
        return Path(sys.executable).resolve().parent / f"{APP_NAME} Data"

    return PROJECT_ROOT


RUNTIME_ROOT = _runtime_root()
ASSETS_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "assets"
DATABASE_PATH = (
    RUNTIME_ROOT / "library.sqlite3"
    if _is_frozen() or os.environ.get("VINQELO_DATA_DIR")
    else PROJECT_ROOT / "database" / "library.sqlite3"
)
LOG_DIR = RUNTIME_ROOT / "logs"
LOG_PATH = LOG_DIR / "vinqelo_player.log"
COVER_CACHE_DIR = RUNTIME_ROOT / "cover_cache"
