"""Lectura segura de metadatos técnicos, álbum y carátulas locales."""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.flac import Picture


LOCAL_COVER_NAMES = (
    "cover.jpg",
    "cover.png",
    "folder.jpg",
    "folder.png",
    "front.jpg",
    "front.png",
)


@dataclass(slots=True)
class TrackDetails:
    file_path: Path
    title: str
    artist: str
    album: str
    album_artist: str
    year: str
    genre: str
    track_number: str
    disc_number: str
    duration_seconds: float
    file_format: str
    codec: str
    bitrate_kbps: int | None
    sample_rate_hz: int | None
    bits_per_sample: int | None
    channels: int | None
    size_bytes: int
    cover_data: bytes | None = None
    cover_origin: str = ""

    @property
    def album_line(self) -> str:
        parts = [self.album]
        if self.album_artist and self.album_artist != "Artista desconocido":
            parts.append(self.album_artist)
        if self.year:
            parts.append(self.year)
        return "  ·  ".join(parts)

    @property
    def catalog_line(self) -> str:
        parts: list[str] = []
        if self.track_number:
            parts.append(f"Pista {self.track_number}")
        if self.disc_number:
            parts.append(f"Disco {self.disc_number}")
        if self.genre:
            parts.append(self.genre)
        return "  ·  ".join(parts)

    @property
    def quality_line(self) -> str:
        parts = [self.file_format]
        if self.codec and self.codec.upper() != self.file_format.upper():
            parts.append(self.codec)
        if self.bits_per_sample:
            parts.append(f"{self.bits_per_sample} bits")
        if self.sample_rate_hz:
            if self.sample_rate_hz % 1000 == 0:
                rate = f"{self.sample_rate_hz // 1000} kHz"
            else:
                rate = f"{self.sample_rate_hz / 1000:.1f} kHz"
            parts.append(rate)
        if self.bitrate_kbps:
            parts.append(f"{self.bitrate_kbps:,} kbps".replace(",", " "))
        if self.channels:
            channel_name = {1: "Mono", 2: "Estéreo"}.get(self.channels, f"{self.channels} canales")
            parts.append(channel_name)
        return "  ·  ".join(parts)

    @property
    def tooltip_text(self) -> str:
        size_mb = self.size_bytes / (1024 * 1024)
        lines = [
            f"Título: {self.title}",
            f"Artista: {self.artist}",
            f"Álbum: {self.album}",
            f"Artista del álbum: {self.album_artist}",
        ]
        if self.year:
            lines.append(f"Año: {self.year}")
        if self.genre:
            lines.append(f"Género: {self.genre}")
        if self.track_number:
            lines.append(f"Pista: {self.track_number}")
        lines.extend((f"Calidad: {self.quality_line}", f"Tamaño: {size_mb:.1f} MB"))
        return "\n".join(lines)


def read_track_details(path: Path) -> TrackDetails:
    """Lee todos los datos disponibles y aplica valores de respaldo claros."""
    path = Path(path)
    logger = logging.getLogger(__name__)
    easy_audio = None
    tags: object = {}

    try:
        easy_audio = MutagenFile(path, easy=True)
        tags = easy_audio.tags if easy_audio is not None and easy_audio.tags else {}
    except Exception:
        logger.warning("No se pudieron leer metadatos fáciles de %s", path, exc_info=True)

    title = _tag(tags, "title") or path.stem
    artist = _tag(tags, "artist") or "Artista desconocido"
    album = _tag(tags, "album") or "Álbum desconocido"
    album_artist = (
        _tag(tags, "albumartist")
        or _tag(tags, "album artist")
        or artist
    )
    date = _tag(tags, "date") or _tag(tags, "originaldate")
    year_match = re.search(r"\b(19|20)\d{2}\b", date)
    year = year_match.group(0) if year_match else ""
    genre = _tag(tags, "genre")
    track_number = _tag(tags, "tracknumber")
    disc_number = _tag(tags, "discnumber")

    info = getattr(easy_audio, "info", None)
    duration = float(getattr(info, "length", 0.0) or 0.0)
    bitrate = int(getattr(info, "bitrate", 0) or 0)
    sample_rate = int(getattr(info, "sample_rate", 0) or 0)
    bits_per_sample = int(getattr(info, "bits_per_sample", 0) or 0)
    channels = int(getattr(info, "channels", 0) or 0)
    file_format = path.suffix.lstrip(".").upper() or "AUDIO"
    codec = _codec_name(easy_audio, info, file_format)

    cover_data, cover_origin = _read_embedded_cover(path)
    if cover_data is None:
        cover_data, cover_origin = _read_folder_cover(path.parent)

    return TrackDetails(
        file_path=path.resolve(),
        title=title,
        artist=artist,
        album=album,
        album_artist=album_artist,
        year=year,
        genre=genre,
        track_number=track_number,
        disc_number=disc_number,
        duration_seconds=duration,
        file_format=file_format,
        codec=codec,
        bitrate_kbps=round(bitrate / 1000) if bitrate else None,
        sample_rate_hz=sample_rate or None,
        bits_per_sample=bits_per_sample or None,
        channels=channels or None,
        size_bytes=path.stat().st_size if path.exists() else 0,
        cover_data=cover_data,
        cover_origin=cover_origin,
    )


def _tag(tags: object, key: str) -> str:
    try:
        value = tags.get(key)  # type: ignore[union-attr]
    except (AttributeError, TypeError):
        return ""
    if isinstance(value, (list, tuple)) and value:
        return str(value[0]).strip()
    return str(value).strip() if value else ""


def _codec_name(audio: object, info: object, file_format: str) -> str:
    codec_description = str(getattr(info, "codec_description", "") or "").strip()
    if codec_description:
        return codec_description
    codec = str(getattr(info, "codec", "") or "").strip()
    if codec:
        return {"mp4a.40.2": "AAC", "alac": "ALAC"}.get(codec.lower(), codec.upper())
    class_name = type(audio).__name__.lower() if audio is not None else ""
    mappings = {
        "mp3": "MP3",
        "flac": "FLAC",
        "wave": "PCM",
        "aiff": "PCM",
        "oggvorbis": "Vorbis",
        "oggopus": "Opus",
        "mp4": "AAC",
        "aac": "AAC",
    }
    return next((name for marker, name in mappings.items() if marker in class_name), file_format)


def _read_embedded_cover(path: Path) -> tuple[bytes | None, str]:
    try:
        audio = MutagenFile(path)
        if audio is None:
            return None, ""

        pictures = getattr(audio, "pictures", None)
        if pictures:
            front = next((picture for picture in pictures if getattr(picture, "type", 0) == 3), pictures[0])
            return bytes(front.data), "Carátula incrustada"

        tags = getattr(audio, "tags", None)
        if tags is None:
            return None, ""

        if hasattr(tags, "getall"):
            pictures = tags.getall("APIC")
            if pictures:
                front = next((picture for picture in pictures if getattr(picture, "type", 0) == 3), pictures[0])
                return bytes(front.data), "Carátula incrustada"

        covers = tags.get("covr") if hasattr(tags, "get") else None
        if covers:
            return bytes(covers[0]), "Carátula incrustada"

        metadata_blocks = tags.get("metadata_block_picture") if hasattr(tags, "get") else None
        if metadata_blocks:
            encoded = metadata_blocks[0] if isinstance(metadata_blocks, (list, tuple)) else metadata_blocks
            picture = Picture(base64.b64decode(encoded))
            return bytes(picture.data), "Carátula incrustada"
    except Exception:
        logging.getLogger(__name__).warning(
            "No se pudo extraer la carátula incrustada de %s",
            path,
            exc_info=True,
        )
    return None, ""


def _read_folder_cover(folder: Path) -> tuple[bytes | None, str]:
    for name in LOCAL_COVER_NAMES:
        candidate = folder / name
        if candidate.is_file():
            try:
                return candidate.read_bytes(), f"Archivo local: {candidate.name}"
            except OSError:
                logging.getLogger(__name__).warning("No se pudo leer %s", candidate, exc_info=True)
    return None, ""
