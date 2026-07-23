"""Escaneo rígido de bibliotecas organizadas como Artista/Álbum/Pista."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
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


ProgressCallback = Callable[[int, int, str], None]


def scan_library(
    root_path: Path,
    *,
    known_tracks: Mapping[str, object] | None = None,
    progress: ProgressCallback | None = None,
) -> LibraryScan:
    root = Path(root_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"La carpeta raíz no existe: {root}")
    result = LibraryScan(root_path=root)
    known = known_tracks or {}
    artist_folders = sorted((p for p in root.iterdir() if p.is_dir()), key=_natural_key)
    album_jobs: list[tuple[Path, Path, list[Path], bool, str, str]] = []
    artist_by_folder: dict[Path, ScannedArtist] = {}
    total_files = 0
    for artist_folder in artist_folders:
        compilation = _looks_like_compilation(artist_folder.name)
        artist = ScannedArtist(
            name="Varios artistas" if compilation else artist_folder.name,
            folder_path=artist_folder.resolve(),
        )
        artist_by_folder[artist.folder_path] = artist
        loose_files = sorted(
            (p for p in artist_folder.iterdir() if is_supported_audio(p)), key=_natural_key
        )
        result.discovered_paths.update(str(path.resolve()) for path in loose_files)
        if loose_files:
            album_jobs.append(
                (
                    artist.folder_path,
                    artist_folder,
                    loose_files,
                    compilation,
                    artist.name,
                    artist_folder.name if compilation else "Pistas sueltas",
                )
            )
            total_files += len(loose_files)
        for album_folder in sorted((p for p in artist_folder.iterdir() if p.is_dir()), key=_natural_key):
            audio_files = sorted(
                (p for p in album_folder.rglob("*") if is_supported_audio(p)), key=_natural_key
            )
            result.discovered_paths.update(str(path.resolve()) for path in audio_files)
            if not audio_files:
                continue
            album_jobs.append(
                (
                    artist.folder_path,
                    album_folder,
                    audio_files,
                    compilation,
                    artist.name,
                    album_folder.name,
                )
            )
            total_files += len(audio_files)

    completed = 0
    if progress:
        progress(0, total_files, root.name)
    for artist_folder, folder, audio_files, compilation, artist_name, title in album_jobs:
        album = _scan_album_files(
            title=title,
            folder=folder,
            audio_files=audio_files,
            compilation=compilation,
            folder_artist=artist_name,
            warnings=result.warnings,
            known_tracks=known,
            progress=(
                lambda current, _total, name, base=completed:
                progress(base + current, total_files, name)
                if progress else None
            ),
        )
        completed += len(audio_files)
        if album is not None:
            artist_by_folder[artist_folder].albums.append(album)

    for artist_folder in artist_folders:
        artist = artist_by_folder[artist_folder.resolve()]
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
    known_tracks: Mapping[str, object] | None = None,
    progress: ProgressCallback | None = None,
) -> ScannedAlbum | None:
    tracks: list[ScannedTrack] = []
    album_year: int | None = None
    known = known_tracks or {}
    for index, audio_path in enumerate(audio_files, start=1):
        try:
            stat = audio_path.stat()
            resolved = audio_path.resolve()
            cached = known.get(str(resolved))
            unchanged = (
                cached is not None
                and int(cached["file_size"] or 0) == int(stat.st_size)
                and int(cached["modified_ns"] or 0) == int(stat.st_mtime_ns)
            )
            if unchanged:
                cached_year = int(cached["album_year"] or 0)
                if album_year is None and cached_year:
                    album_year = cached_year
                tracks.append(
                    ScannedTrack(
                        title=str(cached["title"] or audio_path.stem),
                        track_artist=(
                            str(cached["track_artist"] or "Artista desconocido")
                            if compilation else folder_artist
                        ),
                        track_number=cached["track_number"],
                        file_path=resolved,
                        duration=float(cached["duration"] or 0),
                        file_format=str(cached["file_format"] or audio_path.suffix.lstrip(".")),
                        file_size=int(stat.st_size),
                        modified_ns=int(stat.st_mtime_ns),
                        file_signature=str(cached["file_signature"] or ""),
                    )
                )
            else:
                details = read_track_details(audio_path)
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
                        file_path=resolved,
                        duration=details.duration_seconds,
                        file_format=details.file_format,
                        file_size=int(stat.st_size),
                        modified_ns=int(stat.st_mtime_ns),
                        file_signature=_file_signature(audio_path, int(stat.st_size)),
                    )
                )
        except Exception as exc:
            warnings.append(f"{audio_path.name}: {exc}")
        finally:
            if progress:
                progress(index, len(audio_files), audio_path.name)
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
    progress = Signal(int, int, str)

    def __init__(
        self,
        root_path: Path,
        known_tracks: Mapping[str, object] | None = None,
        database: object | None = None,
    ) -> None:
        super().__init__()
        self.root_path = root_path
        self.known_tracks = dict(known_tracks or {})
        self.database = database

    @Slot()
    def run(self) -> None:
        try:
            scan = scan_library(
                self.root_path,
                known_tracks=self.known_tracks,
                progress=lambda current, total, name: self.progress.emit(
                    round(95 * current / total) if total > 0 else 0,
                    100,
                    name,
                ),
            )
            should_store = bool(scan.artists)
            if self.database is not None and not should_store:
                registered = {
                    str(Path(row["folder_path"]).resolve())
                    for row in self.database.get_roots()
                }
                should_store = str(scan.root_path.resolve()) in registered
            result = (
                self.database.synchronize_library_scan(scan)
                if self.database is not None and should_store else None
            )
            self.progress.emit(100, 100, "Biblioteca actualizada")
            self.finished.emit((scan, result))
        except Exception as exc:
            self.failed.emit(str(exc))


class LibraryRootsSyncWorker(QObject):
    """Escanea varias raíces sin bloquear la interfaz principal."""

    finished = Signal(object, object)
    progress = Signal(int, int, str)

    def __init__(
        self,
        root_paths: list[Path],
        known_tracks: Mapping[str, object] | None = None,
        database: object | None = None,
    ) -> None:
        super().__init__()
        self.root_paths = root_paths
        self.known_tracks = dict(known_tracks or {})
        self.database = database

    @Slot()
    def run(self) -> None:
        scans: list[LibraryScan] = []
        errors: list[str] = []
        root_count = len(self.root_paths)
        for root_index, root_path in enumerate(self.root_paths):
            try:
                scan = scan_library(
                        root_path,
                        known_tracks=self.known_tracks,
                        progress=lambda current, total, name, base=root_index: self.progress.emit(
                            round(
                                100
                                * (
                                    base
                                    + (
                                        0.95 * current / total
                                        if total > 0 else 0
                                    )
                                )
                                / max(1, root_count)
                            ),
                            100,
                            name,
                        ),
                )
                result = (
                    self.database.synchronize_library_scan(scan)
                    if self.database is not None else None
                )
                self.progress.emit(
                    round(100 * (root_index + 1) / max(1, root_count)),
                    100,
                    "Biblioteca actualizada",
                )
                scans.append((scan, result))
            except Exception as exc:
                errors.append(f"{root_path}: {exc}")
        self.finished.emit(scans, errors)
