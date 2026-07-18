"""Escaneo rígido de bibliotecas organizadas como Artista/Álbum/Pista."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from library.audio_formats import is_supported_audio
from library.track_metadata import LOCAL_COVER_NAMES, read_track_details


@dataclass(slots=True)
class ScannedTrack:
    title: str
    track_artist: str
    track_number: int | None
    file_path: Path
    duration: float
    file_format: str
    file_size: int
    modified_ns: int
    file_signature: str


@dataclass(slots=True)
class ScannedAlbum:
    title: str
    folder_path: Path
    cover_path: Path | None
    year: int | None
    is_compilation: bool
    tracks: list[ScannedTrack] = field(default_factory=list)


@dataclass(slots=True)
class ScannedArtist:
    name: str
    folder_path: Path
    albums: list[ScannedAlbum] = field(default_factory=list)


@dataclass(slots=True)
class LibraryScan:
    root_path: Path
    artists: list[ScannedArtist] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    discovered_paths: set[str] = field(default_factory=set)


COMPILATION_FOLDER_NAMES = {
    "varios artistas", "various artists", "compilaciones", "compilations"
}
COMPILATION_WORDS = {
    "varios", "varias", "sueltos", "sueltas", "spotify", "playlist", "mix",
    "salsa", "salsas", "vallenato", "vallenatos", "merengue", "merengues",
    "gaita", "gaitas", "champeta", "champetas", "bailables", "romanticas",
    "románticas", "mtv",
}


def scan_library(root_path: Path) -> LibraryScan:
    root = Path(root_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"La carpeta raíz no existe: {root}")
    result = LibraryScan(root_path=root)
    for artist_folder in sorted((p for p in root.iterdir() if p.is_dir()), key=_natural_key):
        compilation = _looks_like_compilation(artist_folder.name)
        artist = ScannedArtist(
            name="Varios artistas" if compilation else artist_folder.name,
            folder_path=artist_folder.resolve(),
        )
        loose_files = sorted(
            (p for p in artist_folder.iterdir() if is_supported_audio(p)), key=_natural_key
        )
        result.discovered_paths.update(str(path.resolve()) for path in loose_files)
        if loose_files:
            loose_album = _scan_album_files(
                title=artist_folder.name if compilation else "Pistas sueltas",
                folder=artist_folder,
                audio_files=loose_files,
                compilation=compilation,
                folder_artist=artist.name,
                warnings=result.warnings,
            )
            if loose_album is not None:
                artist.albums.append(loose_album)
        for album_folder in sorted((p for p in artist_folder.iterdir() if p.is_dir()), key=_natural_key):
            audio_files = sorted(
                (p for p in album_folder.rglob("*") if is_supported_audio(p)), key=_natural_key
            )
            result.discovered_paths.update(str(path.resolve()) for path in audio_files)
            if not audio_files:
                continue
            album = _scan_album_files(
                title=album_folder.name,
                folder=album_folder,
                audio_files=audio_files,
                compilation=compilation,
                folder_artist=artist.name,
                warnings=result.warnings,
            )
            if album is not None:
                artist.albums.append(album)
        if artist.albums:
            result.artists.append(artist)
    return result


def _scan_album_files(
    *,
    title: str,
    folder: Path,
    audio_files: list[Path],
    compilation: bool,
    folder_artist: str,
    warnings: list[str],
) -> ScannedAlbum | None:
    tracks: list[ScannedTrack] = []
    album_year: int | None = None
    for audio_path in audio_files:
        try:
            details = read_track_details(audio_path)
            stat = audio_path.stat()
            number = _track_number(details.track_number, audio_path.stem)
            if album_year is None and details.year.isdigit():
                album_year = int(details.year)
            tracks.append(
                ScannedTrack(
                    title=details.title or audio_path.stem,
                    track_artist=(
                        getattr(details, "artist", "") or "Artista desconocido"
                        if compilation
                        else folder_artist
                    ),
                    track_number=number,
                    file_path=audio_path.resolve(),
                    duration=details.duration_seconds,
                    file_format=details.file_format,
                    file_size=int(stat.st_size),
                    modified_ns=int(stat.st_mtime_ns),
                    file_signature=_file_signature(audio_path, int(stat.st_size)),
                )
            )
        except Exception as exc:
            warnings.append(f"{audio_path.name}: {exc}")
    if not tracks:
        return None
    return ScannedAlbum(
        title=title,
        folder_path=folder.resolve(),
        cover_path=_find_cover(folder),
        year=album_year,
        is_compilation=compilation,
        tracks=tracks,
    )


def _looks_like_compilation(folder_name: str) -> bool:
    normalized = folder_name.casefold().strip()
    if normalized in COMPILATION_FOLDER_NAMES:
        return True
    words = set(re.findall(r"[\wáéíóúñ]+", normalized, flags=re.UNICODE))
    return bool(words & COMPILATION_WORDS)


def _find_cover(folder: Path) -> Path | None:
    names = {child.name.casefold(): child for child in folder.iterdir() if child.is_file()}
    for name in LOCAL_COVER_NAMES:
        if name in names:
            return names[name].resolve()
    return None


def _track_number(tag_value: str, filename: str) -> int | None:
    match = re.search(r"\d+", tag_value or "") or re.match(r"\s*(\d+)", filename)
    return int(match.group(0)) if match else None


def _natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", path.name)]


def _file_signature(path: Path, size: int | None = None) -> str:
    """Firma ligera para reconocer una pista aunque cambie de ruta o nombre."""
    file_size = int(size if size is not None else path.stat().st_size)
    digest = hashlib.sha1()
    digest.update(str(file_size).encode("ascii"))
    sample_size = 128 * 1024
    with path.open("rb") as stream:
        digest.update(stream.read(sample_size))
        if file_size > sample_size:
            stream.seek(max(0, file_size - sample_size))
            digest.update(stream.read(sample_size))
    return digest.hexdigest()


class LibraryScanWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, root_path: Path) -> None:
        super().__init__()
        self.root_path = root_path

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(scan_library(self.root_path))
        except Exception as exc:
            self.failed.emit(str(exc))


class LibraryRootsSyncWorker(QObject):
    """Escanea varias raíces sin bloquear la interfaz principal."""

    finished = Signal(object, object)

    def __init__(self, root_paths: list[Path]) -> None:
        super().__init__()
        self.root_paths = root_paths

    @Slot()
    def run(self) -> None:
        scans: list[LibraryScan] = []
        errors: list[str] = []
        for root_path in self.root_paths:
            try:
                scans.append(scan_library(root_path))
            except Exception as exc:
                errors.append(f"{root_path}: {exc}")
        self.finished.emit(scans, errors)
