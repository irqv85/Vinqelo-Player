"""Modelo de pista local."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Track:
    album_id: int
    title: str
    file_path: Path
    file_format: str
    track_artist: str | None = None
    track_number: int | None = None
    duration: float = 0.0
    id: int | None = None

