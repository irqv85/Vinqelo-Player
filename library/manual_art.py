"""Imágenes elegidas manualmente por el usuario y protegidas del reemplazo automático."""

from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtGui import QImage

from config import COVER_CACHE_DIR
from library.cover_art import cover_cache_path


def manual_artist_image_path(artist: str) -> Path:
    digest = hashlib.sha256(artist.casefold().encode("utf-8")).hexdigest()
    return COVER_CACHE_DIR / "manual_artists" / f"{digest}.img"


def save_manual_artist_image(artist: str, source: Path) -> bytes:
    return _save_valid_image(source, manual_artist_image_path(artist))


def save_manual_artist_data(artist: str, data: bytes) -> bytes:
    return _save_valid_data(data, manual_artist_image_path(artist))


def manual_album_cover_path(title: str, artist: str) -> Path:
    return cover_cache_path(title, artist)


def manual_album_marker_path(cache_path: Path) -> Path:
    return cache_path.with_name(cache_path.name + ".manual")


def is_manual_album_cover(cache_path: Path) -> bool:
    return manual_album_marker_path(cache_path).is_file()


def save_manual_album_cover(title: str, artist: str, source: Path) -> bytes:
    destination = manual_album_cover_path(title, artist)
    data = _save_valid_image(source, destination)
    marker = manual_album_marker_path(destination)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("manual\n", encoding="utf-8")
    return data


def save_manual_album_data(title: str, artist: str, data: bytes) -> bytes:
    destination = manual_album_cover_path(title, artist)
    saved = _save_valid_data(data, destination)
    marker = manual_album_marker_path(destination)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("manual\n", encoding="utf-8")
    return saved


def read_image(path: Path) -> bytes | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return data if not QImage.fromData(data).isNull() else None


def _save_valid_image(source: Path, destination: Path) -> bytes:
    data = source.read_bytes()
    return _save_valid_data(data, destination)


def _save_valid_data(data: bytes, destination: Path) -> bytes:
    if QImage.fromData(data).isNull():
        raise ValueError("El archivo seleccionado no contiene una imagen válida.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return data
