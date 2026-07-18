"""Integración de Vinqelo con la sesión multimedia nativa de Windows."""

from __future__ import annotations

import hashlib
import logging
import re
import sys
import time
from datetime import timedelta
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from config import APP_NAME, ASSETS_DIR, COVER_CACHE_DIR
from library.track_metadata import TrackDetails


class WindowsMediaSession(QObject):
    """Publica estado y metadatos en SystemMediaTransportControls (SMTC)."""

    action_requested = Signal(str)

    def __init__(self, window_handle: int, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._controls = None
        self._button_token = None
        self._button_enum = None
        self._status_enum = None
        self._timeline_type = None
        self._playback_type = None
        self._stream_reference = None
        self._uri_type = None
        self._current_file = ""
        self._last_timeline_second = -1
        self._last_duration_ms = -1
        self._available = False

        if sys.platform != "win32":
            return
        try:
            from winrt.windows.foundation import Uri
            from winrt.windows.media import (
                MediaPlaybackStatus,
                MediaPlaybackType,
                SystemMediaTransportControlsButton,
                SystemMediaTransportControlsTimelineProperties,
            )
            from winrt.windows.media.interop import get_for_window
            from winrt.windows.storage.streams import RandomAccessStreamReference

            controls = get_for_window(int(window_handle))
            controls.is_play_enabled = True
            controls.is_pause_enabled = True
            controls.is_stop_enabled = True
            controls.is_next_enabled = True
            controls.is_previous_enabled = True
            controls.playback_status = MediaPlaybackStatus.STOPPED
            controls.display_updater.type = MediaPlaybackType.MUSIC
            controls.display_updater.app_media_id = APP_NAME
            self._button_token = controls.add_button_pressed(self._button_pressed)
            self._controls = controls
            self._button_enum = SystemMediaTransportControlsButton
            self._status_enum = MediaPlaybackStatus
            self._timeline_type = SystemMediaTransportControlsTimelineProperties
            self._playback_type = MediaPlaybackType
            self._stream_reference = RandomAccessStreamReference
            self._uri_type = Uri
            self._available = True
            self._logger.info("Sesión multimedia de Windows activada")
        except Exception:
            self._logger.exception("Windows no permitió crear la sesión multimedia")

    @property
    def is_available(self) -> bool:
        return self._available

    def _button_pressed(self, _sender: object, event: object) -> None:
        if self._button_enum is None:
            return
        actions = {
            self._button_enum.PLAY: "play",
            self._button_enum.PAUSE: "pause",
            self._button_enum.STOP: "stop",
            self._button_enum.NEXT: "next",
            self._button_enum.PREVIOUS: "previous",
        }
        action = actions.get(event.button)
        if action:
            self.action_requested.emit(action)

    def set_track_details(self, details: TrackDetails) -> None:
        controls = self._controls
        if controls is None or self._playback_type is None:
            return
        try:
            self._current_file = str(details.file_path)
            updater = controls.display_updater
            updater.type = self._playback_type.MUSIC
            updater.app_media_id = APP_NAME
            music = updater.music_properties
            music.title = details.title or details.file_path.stem
            music.artist = details.artist or "Artista desconocido"
            music.album_title = details.album or "Álbum desconocido"
            music.album_artist = details.album_artist or details.artist
            track_match = re.search(r"\d+", details.track_number or "")
            music.track_number = int(track_match.group()) if track_match else 0
            updater.update()
            controls.is_enabled = True
            self._last_timeline_second = -1
            self._last_duration_ms = -1
            self.update_timeline(0, int(details.duration_seconds * 1000))
            default_artwork = ASSETS_DIR / "icons" / "vinqelo-v.png"
            if default_artwork.is_file():
                self.set_artwork(str(details.file_path), default_artwork.read_bytes())
        except Exception:
            self._logger.exception("No se pudieron actualizar los datos multimedia de Windows")

    def set_artwork(self, file_path: str, data: bytes) -> None:
        controls = self._controls
        if (
            controls is None
            or not data
            or str(Path(file_path)) != str(Path(self._current_file))
            or self._stream_reference is None
            or self._uri_type is None
        ):
            return
        try:
            extension = ".png" if data.startswith(b"\x89PNG") else ".jpg"
            cache = COVER_CACHE_DIR / "windows_media"
            cache.mkdir(parents=True, exist_ok=True)
            key = hashlib.sha1(self._current_file.encode("utf-8")).hexdigest()
            artwork_path = cache / f"{key}{extension}"
            if not artwork_path.exists() or artwork_path.read_bytes() != data:
                artwork_path.write_bytes(data)
            controls.display_updater.thumbnail = self._stream_reference.create_from_uri(
                self._uri_type(artwork_path.resolve().as_uri())
            )
            controls.display_updater.update()
        except Exception:
            self._logger.warning("Windows no pudo cargar la carátula multimedia", exc_info=True)

    def set_playback_state(self, state: str) -> None:
        if self._controls is None or self._status_enum is None:
            return
        status = {
            "playing": self._status_enum.PLAYING,
            "paused": self._status_enum.PAUSED,
            "stopped": self._status_enum.STOPPED,
        }.get(state, self._status_enum.STOPPED)
        try:
            self._controls.playback_status = status
        except Exception:
            self._logger.warning("No se pudo actualizar el estado multimedia", exc_info=True)

    def set_navigation(self, has_previous: bool, has_next: bool) -> None:
        if self._controls is None:
            return
        try:
            self._controls.is_previous_enabled = bool(has_previous)
            self._controls.is_next_enabled = bool(has_next)
        except Exception:
            self._logger.warning("No se pudieron actualizar los botones multimedia", exc_info=True)

    def update_timeline(self, position_ms: int, duration_ms: int) -> None:
        if self._controls is None or self._timeline_type is None:
            return
        position_ms = max(0, int(position_ms))
        duration_ms = max(position_ms, int(duration_ms))
        current_second = position_ms // 1000
        if (
            current_second == self._last_timeline_second
            and duration_ms == self._last_duration_ms
        ):
            return
        self._last_timeline_second = current_second
        self._last_duration_ms = duration_ms
        try:
            timeline = self._timeline_type()
            zero = timedelta(0)
            end = timedelta(milliseconds=duration_ms)
            timeline.start_time = zero
            timeline.min_seek_time = zero
            timeline.position = timedelta(milliseconds=position_ms)
            timeline.max_seek_time = end
            timeline.end_time = end
            self._controls.update_timeline_properties(timeline)
        except Exception:
            if time.monotonic() % 10 < 1:
                self._logger.debug("Windows rechazó la línea de tiempo", exc_info=True)

    def shutdown(self) -> None:
        controls = self._controls
        if controls is None:
            return
        try:
            if self._button_token is not None:
                controls.remove_button_pressed(self._button_token)
            controls.is_enabled = False
            controls.display_updater.clear_all()
            controls.display_updater.update()
        except Exception:
            self._logger.warning("No se pudo cerrar completamente la sesión multimedia", exc_info=True)
        finally:
            self._button_token = None
            self._controls = None
            self._available = False
