"""Exportacion ordenada de playlists a una carpeta plana."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from library.process_utils import hidden_low_priority_process_options


INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

EXPORT_AUDIO_PROFILES = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "128k"],
    "ogg": ["-c:a", "libvorbis", "-b:a", "128k"],
    "wma": ["-c:a", "wmav2", "-b:a", "128k"],
}


def safe_filename(value: object, fallback: str = "Pista") -> str:
    name = INVALID_FILENAME.sub("_", str(value or "")).strip().rstrip(".")
    return name or fallback


class PlaylistExportWorker(QObject):
    """Convierte a 128 kbps, secuencialmente y con prioridad baja."""

    progress = Signal(int, int, str)
    finished = Signal(str, int, object, bool)
    failed = Signal(str)

    def __init__(
        self,
        playlist_name: str,
        tracks: list[dict[str, object]],
        destination: str,
        output_format: str,
    ) -> None:
        super().__init__()
        self.playlist_name = safe_filename(playlist_name, "Playlist")
        self.tracks = tracks
        self.destination = Path(destination)
        self.output_format = output_format.lower().lstrip(".")
        self._logger = logging.getLogger(__name__)
        self._cancelled = False
        self._process: subprocess.Popen[bytes] | None = None

    def cancel(self) -> None:
        self._cancelled = True
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    @Slot()
    def run(self) -> None:
        try:
            target = self.destination / self.playlist_name
            target.mkdir(parents=True, exist_ok=True)
            errors: list[str] = []
            exported = 0
            width = max(2, len(str(max(1, len(self.tracks)))))
            for index, track in enumerate(self.tracks, 1):
                if self._cancelled:
                    break
                source = Path(str(track.get("file_path", "")))
                title = safe_filename(track.get("title"), source.stem or "Pista")
                output = target / f"{index:0{width}d} - {title}.{self.output_format}"
                self.progress.emit(index - 1, len(self.tracks), title)
                try:
                    if not source.is_file():
                        raise FileNotFoundError("el archivo original no existe")
                    # Incluso si la extensión coincide, se reconvierte para
                    # garantizar el perfil fijo de exportación solicitado.
                    self._convert(source, output)
                    if self._cancelled:
                        output.unlink(missing_ok=True)
                        break
                    exported += 1
                except Exception as exc:
                    if not self._cancelled:
                        error = f"{source.name}: {exc}"
                        errors.append(error)
                        self._logger.error(
                            "No se pudo exportar una pista de la playlist: %s",
                            error,
                        )
            self.progress.emit(
                len(self.tracks), len(self.tracks), "Finalizando"
            )
            self.finished.emit(str(target), exported, errors, self._cancelled)
        except Exception as exc:
            self._logger.exception("Falló la exportación de la playlist")
            self.failed.emit(str(exc))

    def _convert(self, source: Path, output: Path) -> None:
        try:
            from imageio_ffmpeg import get_ffmpeg_exe
        except ImportError as exc:
            raise RuntimeError("No esta instalado el componente de conversion") from exc

        if self.output_format not in EXPORT_AUDIO_PROFILES:
            raise ValueError(f"Formato no compatible: {self.output_format}")
        temporary = output.with_name(f".{output.stem}.exportando{output.suffix}")
        command = [
            get_ffmpeg_exe(), "-nostdin", "-hide_banner", "-loglevel", "error",
            "-y", "-i", str(source), "-map_metadata", "0", "-vn", "-threads", "1",
            *EXPORT_AUDIO_PROFILES[self.output_format], str(temporary),
        ]
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            **hidden_low_priority_process_options(),
        )
        _, stderr = self._process.communicate()
        return_code = self._process.returncode
        self._process = None
        if self._cancelled:
            temporary.unlink(missing_ok=True)
            return
        if return_code:
            temporary.unlink(missing_ok=True)
            message = stderr.decode("utf-8", errors="replace").strip()
            if len(message) > 1200:
                message = message[-1200:]
            raise RuntimeError(message or "fallo la conversion")
        temporary.replace(output)
