"""Exportación jerárquica de la biblioteca con prioridad baja."""

from __future__ import annotations

import os
import json
import re
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from library.playlist_exporter import safe_filename


MAX_BITRATES = {"mp3": 128, "wma": 160}
CODECS = {"mp3": "libmp3lame", "wma": "wmav2"}


def build_library_relative_path(track: dict[str, object]) -> Path:
    """Crea una ruta estable Artista/Álbum/Pista para la copia externa."""
    source = Path(str(track["file_path"]))
    album = safe_filename(
        str(track.get("album_title") or source.parent.name),
        "Álbum",
    )
    if bool(track.get("is_compilation")):
        collection = "Compilaciones"
    else:
        collection = safe_filename(
            str(track.get("artist_name") or "Artista desconocido"),
            "Artista desconocido",
        )
    return Path(collection) / album / source.name


def build_playlist_relative_path(
    playlist_name: str,
    position: int,
    track: dict[str, object],
    *,
    smart: bool = False,
) -> Path:
    """Crea una carpeta de lista plana, ordenada y estable."""
    source = Path(str(track["file_path"]))
    section = "Listas inteligentes" if smart else "Listas de reproducción"
    folder = safe_filename(playlist_name, "Lista")
    title = safe_filename(
        str(track.get("title") or source.stem),
        source.stem or "Pista",
    )
    filename = f"{max(1, int(position)):03d} - {title}{source.suffix}"
    return Path(section) / folder / filename


class LibraryExportWorker(QObject):
    progress = Signal(int, int, str)
    finished = Signal(str, int, object, bool, int)
    failed = Signal(str)

    def __init__(
        self,
        tracks: list[dict[str, object]],
        destination: str,
        output_format: str,
        normalize: bool = True,
        sync: bool = True,
    ) -> None:
        super().__init__()
        self.tracks = tracks
        self.destination = Path(destination) / "Vinqelo Library Export"
        self.output_format = output_format
        self.normalize = normalize
        self.sync = sync
        self._cancelled = False
        self._process: subprocess.Popen[bytes] | None = None

    def cancel(self) -> None:
        self._cancelled = True
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()

    @Slot()
    def run(self) -> None:
        try:
            self.destination.mkdir(parents=True, exist_ok=True)
            manifest_path = self.destination / ".vinqelo-sync.json"
            manifest = self._load_manifest(manifest_path) if self.sync else {}
            errors: list[str] = []
            exported = 0
            skipped = 0
            for index, track in enumerate(self.tracks, start=1):
                if self._cancelled:
                    break
                source = Path(str(track["file_path"]))
                relative = Path(str(track["relative_path"]))
                relative = relative.with_name(
                    safe_filename(relative.stem, "Pista")
                    + f".{self.output_format}"
                )
                output = self.destination / relative
                self.progress.emit(index - 1, len(self.tracks), source.name)
                try:
                    if not source.is_file():
                        raise FileNotFoundError("el archivo original no existe")
                    manifest_key = relative.as_posix()
                    signature = self._export_signature(track)
                    if (
                        self.sync
                        and output.is_file()
                        and manifest.get(manifest_key) == signature
                    ):
                        skipped += 1
                        continue
                    output.parent.mkdir(parents=True, exist_ok=True)
                    self._convert(source, output, track)
                    if self._cancelled:
                        output.unlink(missing_ok=True)
                        break
                    exported += 1
                    manifest[manifest_key] = signature
                except Exception as exc:
                    if not self._cancelled:
                        errors.append(f"{source.name}: {exc}")
            if self.sync:
                self._save_manifest(manifest_path, manifest)
            self.finished.emit(
                str(self.destination), exported, errors, self._cancelled, skipped
            )
        except Exception as exc:
            self.failed.emit(str(exc))

    def _convert(
        self, source: Path, output: Path, track: dict[str, object]
    ) -> None:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
        except ImportError as exc:
            raise RuntimeError("No está instalado el componente de conversión") from exc

        maximum = MAX_BITRATES[self.output_format]
        duration = float(track.get("duration") or 0)
        size = int(track.get("file_size") or 0)
        source_rate = (size * 8 / duration / 1000) if duration > 0 and size > 0 else maximum
        bitrate = max(64, min(maximum, round(source_rate / 16) * 16))
        filters: list[str] = []
        if self.normalize:
            gain = self._peak_gain(get_ffmpeg_exe(), source)
            filters.append(f"volume={gain:.2f}dB")
            filters.append("alimiter=limit=0.891251")

        temporary = output.with_name(
            f".{output.stem}.exportando{output.suffix}"
        )
        command = [
            get_ffmpeg_exe(),
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map_metadata",
            "0",
            "-vn",
            "-threads",
            "1",
        ]
        if filters:
            command.extend(["-af", ",".join(filters)])
        command.extend(
            [
                "-c:a",
                CODECS[self.output_format],
                "-b:a",
                f"{bitrate}k",
                str(temporary),
            ]
        )
        self._run_process(command)
        if self._cancelled:
            temporary.unlink(missing_ok=True)
            return
        temporary.replace(output)

    def _peak_gain(self, ffmpeg: str, source: Path) -> float:
        null_target = "NUL" if os.name == "nt" else "/dev/null"
        command = [
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-i",
            str(source),
            "-vn",
            "-af",
            "volumedetect",
            "-f",
            "null",
            null_target,
        ]
        stderr = self._run_process(command, accept_failure=False)
        match = re.search(
            rb"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", stderr
        )
        if not match:
            return 0.0
        maximum = float(match.group(1))
        return max(0.0, min(20.0, -1.0 - maximum))

    def _run_process(
        self, command: list[str], *, accept_failure: bool = False
    ) -> bytes:
        creationflags = (
            subprocess.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 0
        )
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )
        _, stderr = self._process.communicate()
        return_code = self._process.returncode
        self._process = None
        if self._cancelled:
            return stderr
        if return_code and not accept_failure:
            message = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or "falló la conversión")
        return stderr

    def _export_signature(self, track: dict[str, object]) -> str:
        source = (
            str(track.get("file_signature") or "")
            or f'{track.get("file_size", 0)}:{track.get("modified_ns", 0)}'
        )
        return (
            f"{source}|{self.output_format}|"
            f"{MAX_BITRATES[self.output_format]}|normalize={int(self.normalize)}"
        )

    @staticmethod
    def _load_manifest(path: Path) -> dict[str, str]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return (
                {str(key): str(data) for key, data in value.items()}
                if isinstance(value, dict) else {}
            )
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save_manifest(path: Path, manifest: dict[str, str]) -> None:
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
