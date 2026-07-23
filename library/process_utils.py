"""Opciones seguras para procesos auxiliares de conversión."""

from __future__ import annotations

import os
import subprocess


def hidden_low_priority_process_options() -> dict[str, object]:
    """Oculta procesos auxiliares en Windows y evita que roben el foco."""
    if os.name != "nt":
        return {}

    creationflags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    )
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": creationflags,
        "startupinfo": startupinfo,
    }
