"""Búsqueda interactiva de fotos y carátulas disponibles en internet."""

from __future__ import annotations

import json

from PySide6.QtCore import QSize, QUrl, QUrlQuery, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListView,
    QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from config import APP_VERSION
from library.network_policy import internet_access_allowed
from ui.icons import navigation_icon
from ui.i18n import translate_text


class OnlineArtworkDialog(QDialog):
    def __init__(self, parent: QWidget, query: str, *, kind: str, artist: str = "") -> None:
        super().__init__(parent)
        self.setObjectName("artworkPreviewDialog")
        self.setWindowTitle("Buscar imagen en internet")
        self.resize(760, 610)
        self.kind = kind
        self.artist = artist
        self._network = QNetworkAccessManager(self)
        self._images: dict[int, bytes] = {}
        self._pending = 0
        self._specific_artist = False

        layout = QVBoxLayout(self)
        title = QLabel("Elige una imagen")
        title.setObjectName("pageTitle")
        row = QHBoxLayout()
        self.query = QLineEdit(query)
        self.query.setObjectName("librarySearch")
        self.query.addAction(navigation_icon("search", "#8fa7c7"), QLineEdit.ActionPosition.LeadingPosition)
        search = QPushButton("Buscar")
        search.setObjectName("primaryButton")
        search.clicked.connect(self.search)
        self.query.returnPressed.connect(self.search)
        row.addWidget(self.query, 1)
        row.addWidget(search)
        self.status = QLabel("")
        self.status.setObjectName("pageSubtitle")
        self.results = QListWidget()
        self.results.setObjectName("onlineArtworkGrid")
        self.results.setViewMode(QListView.ViewMode.IconMode)
        self.results.setResizeMode(QListView.ResizeMode.Adjust)
        self.results.setIconSize(QSize(150, 150))
        self.results.setGridSize(QSize(176, 190))
        self.results.setSpacing(6)
        self.results.itemSelectionChanged.connect(self._selection_changed)
        self.results.itemDoubleClicked.connect(lambda _item: self.accept())
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.use_button = self.buttons.button(QDialogButtonBox.StandardButton.Save)
        self.use_button.setText("Usar esta imagen")
        self.use_button.setEnabled(False)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(title)
        layout.addLayout(row)
        layout.addWidget(self.status)
        layout.addWidget(self.results, 1)
        layout.addWidget(self.buttons)
        self.search()

    def selected_data(self) -> bytes | None:
        item = self.results.currentItem()
        return self._images.get(id(item)) if item else None

    def search(self) -> None:
        self.results.clear()
        self._images.clear()
        self.status.setText("Buscando opciones…")
        url = QUrl(
            "https://api.deezer.com/search/artist"
            if self.kind == "artist"
            else "https://api.deezer.com/search/album"
        )
        query = QUrlQuery()
        search_text = self.query.text().strip()
        self._specific_artist = self.artist.strip().casefold() not in {"", "varios artistas"}
        query.addQueryItem(
            "q",
            search_text
            if self.kind == "artist"
            else (
                f'artist:"{self.artist}" album:"{search_text}"'
                if self._specific_artist
                else f'album:"{search_text}"'
            ),
        )
        query.addQueryItem("limit", "40")
        url.setQuery(query)
        reply = self._network.get(self._request(url, "application/json"))
        reply.finished.connect(lambda reply=reply: self._search_finished(reply))

    def _search_finished(self, reply: QNetworkReply) -> None:
        try:
            payload = json.loads(bytes(reply.readAll()).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        error = reply.error()
        reply.deleteLater()
        candidates: list[tuple[str, str]] = []
        if error == QNetworkReply.NetworkError.NoError:
            candidates = deezer_artwork_candidates(
                payload,
                kind=self.kind,
                expected_artist=(
                    self.query.text()
                    if self.kind == "artist"
                    else (self.artist if self._specific_artist else "")
                ),
            )
        if not candidates:
            self.status.setText("No se encontraron imágenes. Prueba otra búsqueda.")
            return
        self._pending = len(candidates)
        for label, image_url in candidates:
            image_reply = self._network.get(self._request(QUrl(image_url), "image/*"))
            image_reply.finished.connect(
                lambda reply=image_reply, label=label: self._image_finished(reply, label)
            )

    def _image_finished(self, reply: QNetworkReply, label: str) -> None:
        data = bytes(reply.readAll())
        error = reply.error()
        reply.deleteLater()
        self._pending -= 1
        pixmap = QPixmap()
        if error == QNetworkReply.NetworkError.NoError and pixmap.loadFromData(data):
            item = QListWidgetItem(QIcon(pixmap), label)
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.results.addItem(item)
            self._images[id(item)] = data
        self.status.setText(
            f"{self.results.count()} opciones encontradas"
            if self._pending == 0
            else "Cargando miniaturas…"
        )

    def _selection_changed(self) -> None:
        self.use_button.setEnabled(self.selected_data() is not None)

    @staticmethod
    def _request(url: QUrl, accept: str) -> QNetworkRequest:
        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", f"VinqeloPlayer/{APP_VERSION}".encode("ascii"))
        request.setRawHeader(b"Accept", accept.encode("ascii"))
        request.setTransferTimeout(15_000)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        return request


def deezer_artwork_candidates(
    payload: object, *, kind: str, expected_artist: str
) -> list[tuple[str, str]]:
    """Extrae únicamente fotos y carátulas pertenecientes al catálogo musical."""
    if not isinstance(payload, dict):
        return []
    expected = _normalized(expected_artist)
    candidates: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for result in payload.get("data", []):
        if not isinstance(result, dict):
            continue
        artist_data = result if kind == "artist" else result.get("artist", {})
        artist_name = str(artist_data.get("name", "")) if isinstance(artist_data, dict) else ""
        normalized_artist = _normalized(artist_name)
        if expected and not (
            expected == normalized_artist
            or expected in normalized_artist
            or normalized_artist in expected
        ):
            continue
        if kind == "artist":
            image_url = result.get("picture_xl") or result.get("picture_big") or result.get("picture_medium")
            label = artist_name
        else:
            image_url = result.get("cover_xl") or result.get("cover_big") or result.get("cover_medium")
            label = f'{result.get("title", "Álbum")} · {artist_name}'
        if image_url and image_url not in seen_urls:
            seen_urls.add(str(image_url))
            candidates.append((label, str(image_url)))
    return candidates[:30]


def _normalized(value: str) -> str:
    return " ".join(value.casefold().replace("&", "and").split())


def choose_online_artwork(parent: QWidget, query: str, *, kind: str, artist: str = "") -> bytes | None:
    if not internet_access_allowed():
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            parent,
            translate_text("Modo local"),
            translate_text(
                "Las búsquedas en internet están desactivadas en Configuración."
            ),
        )
        return None
    dialog = OnlineArtworkDialog(parent, query, kind=kind, artist=artist)
    return dialog.selected_data() if dialog.exec() == QDialog.DialogCode.Accepted else None
