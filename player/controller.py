"""Controlador de reproducción local basado en python-vlc."""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

from mutagen import File as MutagenFile
from PySide6.QtCore import QObject, QTimer, Signal

from library.audio_formats import SUPPORTED_AUDIO_EXTENSIONS


class PlaybackState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class PlayerUnavailableError(RuntimeError):
    """El motor nativo de VLC no está disponible."""


class PlayerController(QObject):
    """Encapsula VLC y expone señales seguras para la interfaz Qt."""

    state_changed = Signal(str)
    position_changed = Signal(int, int)
    track_changed = Signal(str, str, str)
    queue_navigation_changed = Signal(bool, bool)
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._state = PlaybackState.STOPPED
        self._queue: list[Path] = []
        self._current_index = -1
        self._media = None
        self._volume = 70
        self._ended_handled = False

        try:
            import vlc

            self._vlc = vlc
            self._instance = vlc.Instance("--no-video", "--quiet")
            self._player = self._instance.media_player_new()
            if self._player is None:
                raise RuntimeError("VLC no pudo crear un reproductor de audio")
            self._logger.info(
                "Motor VLC disponible: %s",
                vlc.libvlc_get_version().decode("utf-8", errors="replace"),
            )
        except Exception as exc:
            self._logger.exception("No se pudo inicializar VLC")
            raise PlayerUnavailableError(
                "No se encontró una instalación funcional de VLC. "
                "Instala VLC Media Player de 64 bits y reinicia Vinqelo Player."
            ) from exc

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._poll_player)

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def current_file(self) -> Path | None:
        if 0 <= self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None

    def open_file(self, file_path: Path) -> bool:
        """Reemplaza la cola por un archivo y lo reproduce."""
        return self.set_queue([file_path], start_index=0, autoplay=True)

    def set_queue(
        self,
        file_paths: list[Path],
        *,
        start_index: int = 0,
        autoplay: bool = True,
    ) -> bool:
        valid_paths: list[Path] = []
        for candidate in file_paths:
            path = Path(candidate).expanduser().resolve()
            if not path.is_file():
                self._emit_error(f"El archivo no existe: {path}")
                continue
            if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
                self._emit_error(f"Formato de audio no compatible: {path.suffix or 'sin extensión'}")
                continue
            valid_paths.append(path)

        if not valid_paths:
            return False
        if not 0 <= start_index < len(valid_paths):
            self._emit_error("La pista inicial no pertenece a la cola de reproducción.")
            return False

        self.stop(clear_track=False)
        self._queue = valid_paths
        self._current_index = start_index
        return self._load_current(autoplay=autoplay)

    def _load_current(self, *, autoplay: bool) -> bool:
        path = self.current_file
        if path is None:
            self._emit_error("No hay una pista seleccionada.")
            return False

        try:
            self._media = self._instance.media_new(str(path))
            self._player.set_media(self._media)
            self._player.audio_set_volume(self._volume)
            self._ended_handled = False

            title, artist = read_display_metadata(path)
            self.track_changed.emit(title, artist, str(path))
            self.position_changed.emit(0, 0)
            self._emit_queue_navigation()

            if autoplay:
                return self.play()
            self._set_state(PlaybackState.STOPPED)
            return True
        except Exception as exc:
            self._logger.exception("No se pudo cargar el archivo %s", path)
            self._emit_error(f"No se pudo abrir el archivo de audio: {path.name}. Detalle: {exc}")
            return False

    def play(self) -> bool:
        if self.current_file is None:
            self._emit_error("Primero abre un archivo de audio.")
            return False
        try:
            if self._player.play() == -1:
                raise RuntimeError("VLC rechazó el archivo")
            self._player.audio_set_volume(self._volume)
            self._timer.start()
            self._ended_handled = False
            self._set_state(PlaybackState.PLAYING)
            return True
        except Exception as exc:
            self._logger.exception("VLC no pudo iniciar la reproducción")
            self._emit_error(f"El archivo no se pudo reproducir. Detalle: {exc}")
            return False

    def play_pause(self) -> None:
        if self._state is PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()

    def pause(self) -> None:
        if self._state is not PlaybackState.PLAYING:
            return
        try:
            self._player.set_pause(1)
            self._set_state(PlaybackState.PAUSED)
        except Exception as exc:
            self._logger.exception("No se pudo pausar la reproducción")
            self._emit_error(f"No se pudo pausar la reproducción. Detalle: {exc}")

    def stop(self, *, clear_track: bool = False) -> None:
        try:
            self._player.stop()
        except Exception:
            self._logger.exception("No se pudo detener VLC")
        self._timer.stop()
        self._ended_handled = False
        self._set_state(PlaybackState.STOPPED)
        self.position_changed.emit(0, max(0, self._safe_length()))
        if clear_track:
            self._queue.clear()
            self._current_index = -1
            self._media = None
            self._emit_queue_navigation()

    def seek_to(self, milliseconds: int) -> None:
        if self.current_file is None:
            return
        duration = self._safe_length()
        target = max(0, min(int(milliseconds), duration if duration > 0 else int(milliseconds)))
        try:
            self._player.set_time(target)
            self.position_changed.emit(target, max(duration, target))
        except Exception as exc:
            self._logger.exception("No se pudo cambiar la posición")
            self._emit_error(f"No se pudo cambiar la posición. Detalle: {exc}")

    def skip(self, seconds: int) -> None:
        current = max(0, int(self._player.get_time()))
        self.seek_to(current + (seconds * 1000))

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, int(volume)))
        try:
            self._player.audio_set_volume(self._volume)
        except Exception as exc:
            self._logger.exception("No se pudo cambiar el volumen")
            self._emit_error(f"No se pudo cambiar el volumen. Detalle: {exc}")

    def previous(self) -> None:
        if self.current_file is None:
            return
        if self._player.get_time() > 3000 or self._current_index <= 0:
            self.seek_to(0)
            return
        self._current_index -= 1
        self._load_current(autoplay=True)

    def next(self) -> None:
        if self._current_index + 1 >= len(self._queue):
            return
        self._current_index += 1
        self._load_current(autoplay=True)

    def _poll_player(self) -> None:
        try:
            vlc_state = self._player.get_state()
            duration = self._safe_length()
            current = max(0, int(self._player.get_time()))
            self.position_changed.emit(current, duration)

            if vlc_state == self._vlc.State.Ended and not self._ended_handled:
                self._ended_handled = True
                if self._current_index + 1 < len(self._queue):
                    self.next()
                else:
                    self._timer.stop()
                    self._set_state(PlaybackState.STOPPED)
                    self.position_changed.emit(duration, duration)
            elif vlc_state == self._vlc.State.Error:
                self._timer.stop()
                self._set_state(PlaybackState.STOPPED)
                self._emit_error("VLC no pudo decodificar o reproducir este archivo.")
            elif vlc_state == self._vlc.State.Playing:
                self._set_state(PlaybackState.PLAYING)
            elif vlc_state == self._vlc.State.Paused:
                self._set_state(PlaybackState.PAUSED)
        except Exception as exc:
            self._timer.stop()
            self._logger.exception("Error al consultar el estado de VLC")
            self._emit_error(f"Se perdió la comunicación con VLC. Detalle: {exc}")

    def _safe_length(self) -> int:
        try:
            return max(0, int(self._player.get_length()))
        except Exception:
            return 0

    def _set_state(self, state: PlaybackState) -> None:
        if self._state is state:
            return
        self._state = state
        self.state_changed.emit(state.value)

    def _emit_queue_navigation(self) -> None:
        self.queue_navigation_changed.emit(
            self._current_index > 0,
            0 <= self._current_index < len(self._queue) - 1,
        )

    def _emit_error(self, message: str) -> None:
        self._logger.warning(message)
        self.error_occurred.emit(message)

    def shutdown(self) -> None:
        self._timer.stop()
        try:
            self._player.stop()
            self._player.release()
            self._instance.release()
        except Exception:
            self._logger.exception("No se pudo liberar completamente el motor VLC")


def read_display_metadata(path: Path) -> tuple[str, str]:
    """Obtiene título y artista, usando el nombre del archivo como respaldo."""
    title = path.stem
    artist = "Artista desconocido"
    try:
        audio = MutagenFile(path, easy=True)
        if audio is None or not audio.tags:
            return title, artist
        title = _first_tag(audio.tags.get("title")) or title
        artist = _first_tag(audio.tags.get("artist")) or artist
    except Exception:
        logging.getLogger(__name__).warning(
            "No se pudieron leer los metadatos de %s; se usará el nombre del archivo",
            path,
            exc_info=True,
        )
    return title, artist


def _first_tag(value: object) -> str:
    if isinstance(value, (list, tuple)) and value:
        return str(value[0]).strip()
    if isinstance(value, str):
        return value.strip()
    return ""
