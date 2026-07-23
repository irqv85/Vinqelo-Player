"""Búsqueda en segundo plano de portadas y collages de álbumes."""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, QUrlQuery, Signal
from PySide6.QtGui import QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from config import APP_VERSION, COVER_CACHE_DIR
from library.cover_art import (
    cover_cache_path,
    musicbrainz_release_group_query,
    select_original_album_groups,
)
from library.manual_art import is_manual_album_cover, read_image
from library.network_policy import internet_access_allowed


USER_AGENT = f"VinqeloPlayer/{APP_VERSION} (desktop music library)"


class ArtistCollageService(QObject):
    """Procesa una sola cola para respetar el límite de MusicBrainz."""

    cover_ready = Signal(str, bytes)
    album_cover_ready = Signal(int, bytes)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._queue: deque[dict[str, object]] = deque()
        self._requested: set[str] = set()
        self._active = False
        self._last_search = 0.0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._start_next)
        self._task: dict[str, object] = {}
        self._candidate_ids: list[str] = []
        self._found = 0

    def request_album(
        self,
        album_id: int,
        title: str,
        artist: str,
        local_cover: str | None,
    ) -> None:
        if title == "Pistas sueltas":
            return
        if not internet_access_allowed():
            data = _read_image(Path(local_cover)) if local_cover else None
            if data:
                self.album_cover_ready.emit(album_id, data)
                self.cover_ready.emit(artist, data)
            return
        key = f"album\0{artist.casefold()}\0{title.casefold()}"
        cache = cover_cache_path(title, artist)
        data = _read_image(cache)
        if data:
            self.album_cover_ready.emit(album_id, data)
            self.cover_ready.emit(artist, data)
            return
        if key in self._requested:
            return
        self._requested.add(key)
        self._queue.append(
            {
                "kind": "album", "album_id": album_id, "title": title,
                "artist": artist, "local_cover": local_cover or "",
            }
        )
        self._start_next()

    def request(self, artist: str) -> None:
        """Busca discografía cuando el artista solo tiene Pistas sueltas."""
        if not internet_access_allowed():
            return
        key = f"collage\0{artist.casefold()}"
        cached = collage_cache_files(artist)
        for path in cached[:4]:
            data = _read_image(path)
            if data:
                self.cover_ready.emit(artist, data)
        if len(cached) < 4:
            if key in self._requested:
                return
            self._requested.add(key)
            self._queue.append({"kind": "collage", "artist": artist})
            self._start_next()

    def _start_next(self) -> None:
        if not internet_access_allowed():
            self._queue.clear()
            self._active = False
            return
        if self._active or not self._queue:
            return
        elapsed = int((time.monotonic() - self._last_search) * 1000)
        if elapsed < 1100:
            self._timer.start(1100 - elapsed)
            return
        self._active = True
        self._task = self._queue.popleft()
        artist = str(self._task["artist"])
        kind = self._task["kind"]
        self._found = len(collage_cache_files(artist)) if kind == "collage" else 0
        url = QUrl("https://musicbrainz.org/ws/2/release-group/")
        query = QUrlQuery()
        query.addQueryItem(
            "query",
            musicbrainz_release_group_query(str(self._task["title"]), artist)
            if kind == "album"
            else f'artist:"{_escape(artist)}" AND primarytype:Album',
        )
        query.addQueryItem("fmt", "json")
        query.addQueryItem("limit", "16")
        url.setQuery(query)
        self._last_search = time.monotonic()
        reply = self._network.get(_request(url, "application/json"))
        reply.finished.connect(lambda reply=reply: self._search_done(reply))

    def _search_done(self, reply: QNetworkReply) -> None:
        payload = _json_reply(reply)
        groups = payload.get("release-groups", []) if payload else []
        artist = str(self._task["artist"])
        if self._task["kind"] == "album":
            selected = select_original_album_groups(
                groups, str(self._task["title"]), artist
            )
        else:
            selected = _original_artist_albums(groups, artist)
        self._candidate_ids = [
            str(group["id"]) for group in selected if isinstance(group, dict) and group.get("id")
        ]
        self._request_candidate()

    def _request_candidate(self) -> None:
        target = 1 if self._task.get("kind") == "album" else 4
        if self._found >= target or not self._candidate_ids:
            self._complete()
            return
        mbid = self._candidate_ids.pop(0)
        url = QUrl(f"https://coverartarchive.org/release-group/{mbid}/front-500")
        reply = self._network.get(_request(url, "image/*"))
        reply.finished.connect(lambda reply=reply: self._cover_done(reply))

    def _cover_done(self, reply: QNetworkReply) -> None:
        data = bytes(reply.readAll())
        error = reply.error()
        reply.deleteLater()
        if error == QNetworkReply.NetworkError.NoError and _is_image(data):
            artist = str(self._task["artist"])
            if self._task["kind"] == "album":
                cache = cover_cache_path(str(self._task["title"]), artist)
                album_id = int(self._task["album_id"])
                if is_manual_album_cover(cache):
                    manual_data = read_image(cache)
                    if manual_data:
                        data = manual_data
                else:
                    _write_image(cache, data)
                self.album_cover_ready.emit(album_id, data)
            else:
                cache = collage_cache_dir(artist) / f"{self._found:02d}.img"
                _write_image(cache, data)
            self._found += 1
            self.cover_ready.emit(artist, data)
        self._request_candidate()

    def _complete(self) -> None:
        if self._task.get("kind") == "album" and self._found == 0:
            local = Path(str(self._task.get("local_cover", "")))
            data = _read_image(local)
            if data:
                self.album_cover_ready.emit(int(self._task["album_id"]), data)
                self.cover_ready.emit(str(self._task["artist"]), data)
        self._active = False
        self._candidate_ids = []
        self._task = {}
        self._start_next()


def _original_artist_albums(groups: list[object], artist: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        secondary = {str(value).casefold() for value in group.get("secondary-types", [])}
        if "compilation" in secondary or str(group.get("primary-type", "")).casefold() != "album":
            continue
        credits = group.get("artist-credit", [])
        names = {
            str(credit.get("artist", {}).get("name", "")).casefold()
            for credit in credits if isinstance(credit, dict)
        }
        if artist.casefold() in names:
            result.append(group)
    return result


def collage_cache_dir(artist: str) -> Path:
    digest = hashlib.sha256(("album-collage-v1\0" + artist.casefold()).encode("utf-8")).hexdigest()
    return COVER_CACHE_DIR / "artist_collages" / digest


def collage_cache_files(artist: str) -> list[Path]:
    folder = collage_cache_dir(artist)
    return sorted(folder.glob("*.img")) if folder.is_dir() else []


def artist_thumbnail_path(artist: str) -> Path:
    digest = hashlib.sha256(
        ("artist-thumbnail-v1\0" + artist.casefold()).encode("utf-8")
    ).hexdigest()
    return COVER_CACHE_DIR / "artist_thumbnails" / f"{digest}.png"


def _read_image(path: Path) -> bytes | None:
    try:
        data = path.read_bytes()
        return data if _is_image(data) else None
    except (OSError, ValueError):
        return None


def _write_image(path: Path, data: bytes) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError:
        pass


def _json_reply(reply: QNetworkReply) -> dict[str, object]:
    data = bytes(reply.readAll())
    error = reply.error()
    reply.deleteLater()
    if error != QNetworkReply.NetworkError.NoError:
        return {}
    try:
        value = json.loads(data.decode("utf-8"))
        return value if isinstance(value, dict) else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _request(url: QUrl, accept: str) -> QNetworkRequest:
    request = QNetworkRequest(url)
    request.setRawHeader(b"User-Agent", USER_AGENT.encode("ascii"))
    request.setRawHeader(b"Accept", accept.encode("ascii"))
    request.setTransferTimeout(12_000)
    request.setAttribute(
        QNetworkRequest.Attribute.RedirectPolicyAttribute,
        QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
    )
    return request


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').strip()


def _is_image(data: bytes) -> bool:
    return bool(data) and not QImage.fromData(data).isNull()
