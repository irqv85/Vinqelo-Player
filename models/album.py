"""Modelo de album o compilacion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Album:
    title: str
    album_artist: str
    folder_path: Path
    cover_path: Path | None = None
    year: int | None = None
    is_compilation: bool = False
    id: int | None = None

