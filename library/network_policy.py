"""Preferencia central para impedir cualquier consulta automática a internet."""

from PySide6.QtCore import QSettings


def internet_access_allowed() -> bool:
    settings = QSettings("Vinqelo", "Vinqelo Player")
    return not settings.value("privacy/offline_mode", False, type=bool)
