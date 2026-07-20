"""Marca el ejecutable creado exclusivamente para Microsoft Store."""

from __future__ import annotations

import os


os.environ["VINQELO_STORE_BUILD"] = "1"
