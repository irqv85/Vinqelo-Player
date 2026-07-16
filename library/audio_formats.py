"""Formatos admitidos por la biblioteca."""

from __future__ import annotations

from pathlib import Path


SUPPORTED_AUDIO_EXTENSIONS = frozenset({".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac"})


def is_supported_audio(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

