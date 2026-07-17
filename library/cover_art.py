"""Obtención asíncrona de carátulas mediante MusicBrainz y Cover Art Archive."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, QUrlQuery, Signal
from PySide6.QtGui import QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from config import APP_VERSION, COVER_CACHE_DIR
from library.track_metadata import TrackDetails


MUSICBRAINZ_USER_AGENT = (
    f"VinqeloPlayer/{APP_VERSION} (https://github.com/irqv85/Vinqelo-Player)"
)
MINIMUM_SEARCH_INTERVAL_MS = 1100


class CoverArtService(QObject):
    cover_ready = Signal(str, bytes, str)
    cover_unavailable = Signal(str)
    metadata_ready = Signal(str, object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._network = QNetworkAccessManager(self)
        self._current_key = ""
        self._pending: tuple[str, TrackDetails, Path] | None = None
        self._last_search_started = 0.0

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._start_pending_search)

    def request_cover(self, details: TrackDetails) -> None:
        key = str(details.file_path)
        self._current_key = key
        self._pending = None
        self._search_timer.stop()

        if details.album_artist == "Artista desconocido":
            QTimer.singleShot(0, lambda: self._emit_fallback(key, details))
            return

        cache_path = cover_cache_path(details.album, details.album_artist)
        if cache_path.is_file():
            try:
                data = cache_path.read_bytes()
                if _is_image(data):
                    QTimer.singleShot(
                        0,
                        lambda: self.cover_ready.emit(key, data, "Caché local de MusicBrainz"),
                    )
                    return
            except OSError:
                self._logger.warning("No se pudo leer la carátula en caché %s", cache_path)

        self._pending = (key, details, cache_path)
        elapsed_ms = int((time.monotonic() - self._last_search_started) * 1000)
        delay = max(0, MINIMUM_SEARCH_INTERVAL_MS - elapsed_ms)
        if delay:
            self._search_timer.start(delay)
        else:
            self._start_pending_search()

    def _start_pending_search(self) -> None:
        if self._pending is None:
            return
        key, details, cache_path = self._pending
        self._pending = None
        if key != self._current_key:
            return

        loose_track = details.album in {"Pistas sueltas", "Álbum desconocido"}
        url = QUrl(
            "https://musicbrainz.org/ws/2/recording/"
            if loose_track
            else "https://musicbrainz.org/ws/2/release-group/"
        )
        query = QUrlQuery()
        query.addQueryItem(
            "query",
            musicbrainz_recording_query(details.title, details.artist)
            if loose_track
            else musicbrainz_release_group_query(details.album, details.album_artist),
        )
        query.addQueryItem("fmt", "json")
        query.addQueryItem("limit", "5")
        url.setQuery(query)

        request = self._request(url, accept="application/json")
        self._last_search_started = time.monotonic()
        reply = self._network.get(request)
        reply.finished.connect(
            lambda reply=reply, key=key, details=details, cache_path=cache_path, loose=loose_track: self._handle_search_reply(
                reply, key, details, cache_path, loose
            )
        )

    def _handle_search_reply(
        self,
        reply: QNetworkReply,
        key: str,
        details: TrackDetails,
        cache_path: Path,
        loose_track: bool,
    ) -> None:
        data = bytes(reply.readAll())
        error = reply.error()
        error_text = reply.errorString()
        reply.deleteLater()

        if key != self._current_key:
            return
        if error != QNetworkReply.NetworkError.NoError:
            self._logger.info("MusicBrainz no respondió: %s", error_text)
            self._emit_fallback(key, details)
            return

        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            self._logger.warning("MusicBrainz devolvió una respuesta no válida")
            self._emit_fallback(key, details)
            return

        if loose_track:
            recordings = payload.get("recordings", [])
            if not recordings:
                self._emit_fallback(key, details)
                return
            recording = recordings[0]
            releases = recording.get("releases", [])
            if not releases:
                self._emit_fallback(key, details)
                return
            release = releases[0]
            album = release.get("title") or details.album
            date = release.get("date") or ""
            enriched = replace(
                details,
                title=recording.get("title") or details.title,
                album=album,
                year=date[:4] if re.match(r"\d{4}", date) else details.year,
            )
            self.metadata_ready.emit(key, enriched)
            cache_path = cover_cache_path(album, details.artist)
        else:
            groups = payload.get("release-groups", [])
            releases = select_original_album_groups(
                groups, details.album, details.album_artist
            )
            if releases:
                release = releases[0]
                date = release.get("first-release-date") or ""
                enriched = replace(
                    details,
                    album=release.get("title") or details.album,
                    year=date[:4] if re.match(r"\d{4}", date) else details.year,
                )
                self.metadata_ready.emit(key, enriched)

        release_ids = [
            item.get("id")
            for item in releases
            if isinstance(item, dict) and item.get("id")
        ]
        if not release_ids:
            self._emit_fallback(key, details)
            return

        self._request_cover_candidate(
            key, details, cache_path, release_ids, release_group=not loose_track
        )

    def _request_cover_candidate(
        self,
        key: str,
        details: TrackDetails,
        cache_path: Path,
        release_ids: list[str],
        *,
        release_group: bool,
    ) -> None:
        if key != self._current_key:
            return
        if not release_ids:
            self._emit_fallback(key, details)
            return

        release_id, *remaining_ids = release_ids
        entity = "release-group" if release_group else "release"
        image_url = QUrl(f"https://coverartarchive.org/{entity}/{release_id}/front-500")
        image_reply = self._network.get(self._request(image_url, accept="image/*"))
        image_reply.finished.connect(
            lambda reply=image_reply, key=key, details=details, cache_path=cache_path, remaining=remaining_ids, release_group=release_group: self._handle_image_reply(
                reply, key, details, cache_path, remaining, release_group
            )
        )

    def _handle_image_reply(
        self,
        reply: QNetworkReply,
        key: str,
        details: TrackDetails,
        cache_path: Path,
        remaining_ids: list[str],
        release_group: bool,
    ) -> None:
        data = bytes(reply.readAll())
        error = reply.error()
        error_text = reply.errorString()
        reply.deleteLater()

        if key != self._current_key:
            return
        if error != QNetworkReply.NetworkError.NoError or not _is_image(data):
            self._logger.info("Portada no disponible para un lanzamiento: %s", error_text)
            self._request_cover_candidate(
                key,
                details,
                cache_path,
                remaining_ids,
                release_group=release_group,
            )
            return

        from library.manual_art import is_manual_album_cover, read_image

        if is_manual_album_cover(cache_path):
            manual_data = read_image(cache_path)
            if manual_data:
                self.cover_ready.emit(key, manual_data, "Carátula elegida manualmente")
                return

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(data)
        except OSError:
            self._logger.warning("No se pudo guardar la carátula en %s", cache_path, exc_info=True)

        self.cover_ready.emit(key, data, "Cover Art Archive / MusicBrainz")

    def _emit_fallback(self, key: str, details: TrackDetails) -> None:
        if key != self._current_key:
            return
        if details.cover_data and _is_image(details.cover_data):
            self.cover_ready.emit(key, details.cover_data, details.cover_origin or "Carátula incrustada")
        else:
            self.cover_unavailable.emit(key)

    @staticmethod
    def _request(url: QUrl, *, accept: str) -> QNetworkRequest:
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", MUSICBRAINZ_USER_AGENT.encode("utf-8"))
        request.setRawHeader(b"Accept", accept.encode("ascii"))
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        request.setTransferTimeout(12_000)
        return request


def musicbrainz_release_query(album: str, artist: str) -> str:
    return f'release:"{_escape_lucene(album)}" AND artist:"{_escape_lucene(artist)}"'


def musicbrainz_release_group_query(album: str, artist: str) -> str:
    search_album = clean_album_search_title(album, artist)
    return (
        f'release:"{_escape_lucene(search_album)}" AND '
        f'artist:"{_escape_lucene(artist)}" AND primarytype:Album'
    )


def clean_album_search_title(album: str, artist: str) -> str:
    """Quita prefijos organizativos sin modificar el nombre guardado."""
    parts = [part.strip() for part in re.split(r"\s+[-–—]\s+", album) if part.strip()]
    if parts and parts[0].casefold() == artist.casefold():
        parts.pop(0)
    if parts and re.fullmatch(r"(?:19|20)\d{2}", parts[0]):
        parts.pop(0)
    cleaned = " - ".join(parts).strip()
    cleaned = re.sub(r"^\s*[(\[]?(?:19|20)\d{2}[)\]]?\s*[-–—]?\s*", "", cleaned)
    return cleaned or album.strip()


def select_original_album_groups(
    groups: list[object], album: str, artist: str
) -> list[dict[str, object]]:
    """Prioriza título y artista exactos, excluyendo recopilatorios."""
    valid: list[dict[str, object]] = []
    for value in groups:
        if not isinstance(value, dict):
            continue
        secondary = {
            str(item).casefold() for item in value.get("secondary-types", [])
        }
        if "compilation" in secondary:
            continue
        if str(value.get("primary-type", "")).casefold() != "album":
            continue
        credits = value.get("artist-credit", [])
        credit_names = {
            str(credit.get("artist", {}).get("name", "")).casefold()
            for credit in credits
            if isinstance(credit, dict)
        }
        if artist.casefold() not in credit_names:
            continue
        valid.append(value)
    expected_title = clean_album_search_title(album, artist).casefold()
    exact = [
        value for value in valid
        if str(value.get("title", "")).casefold() == expected_title
    ]
    return exact or valid


def musicbrainz_recording_query(title: str, artist: str) -> str:
    clean_title = clean_track_title(title, artist)
    return f'recording:"{_escape_lucene(clean_title)}" AND artist:"{_escape_lucene(artist)}"'


def clean_track_title(title: str, artist: str) -> str:
    cleaned = re.sub(r"(?:https?://)?(?:www\.)?[\w.-]+\.(?:com|net|org)\S*", "", title, flags=re.I)
    if artist and artist != "Artista desconocido":
        escaped_artist = re.escape(artist)
        cleaned = re.sub(rf"\s+(?:de|by|-|–|—)\s*{escaped_artist}\s*$", "", cleaned, flags=re.I)
        cleaned = re.sub(rf"^\s*{escaped_artist}\s*[-–—]\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*[-–—|]+\s*$", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip() or title.strip()


def cover_cache_path(album: str, artist: str) -> Path:
    cache_key = f"album-exact-v2\0{artist.casefold()}\0{album.casefold()}".encode("utf-8")
    return COVER_CACHE_DIR / f"{hashlib.sha256(cache_key).hexdigest()}.img"


def _escape_lucene(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return escaped.strip()


def _is_image(data: bytes) -> bool:
    return bool(data) and not QImage.fromData(data).isNull()
