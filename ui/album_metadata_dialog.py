"""Búsqueda y confirmación de títulos oficiales para un álbum."""

from __future__ import annotations

import json

from PySide6.QtCore import QUrl, QUrlQuery, Signal, Qt
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from config import APP_VERSION
from database.manager import DatabaseManager
from library.network_policy import internet_access_allowed


class AlbumMetadataDialog(QDialog):
    metadata_applied = Signal(object)

    def __init__(self, database: DatabaseManager, album_id: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.database = database
        self.album_id = album_id
        self.album = database.get_album_by_id(album_id)
        self.local_tracks = database.get_tracks_for_album(album_id)
        self.network = QNetworkAccessManager(self)
        self.setWindowTitle("Buscar datos oficiales del álbum")
        self.resize(850, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)
        title = QLabel("Validar títulos con MusicBrainz")
        title.setObjectName("pageTitle")
        artist = self.album["artist_name"] or self.album["album_artist"]
        subtitle = QLabel(f'{artist} · {self.album["title"]} · {len(self.local_tracks)} pistas locales')
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        self.status = QLabel("Buscando ediciones musicales…")
        self.status.setObjectName("mutedLabel")
        root.addWidget(self.status)
        self.releases = QListWidget()
        self.releases.setMaximumHeight(145)
        self.releases.currentItemChanged.connect(self._release_selected)
        root.addWidget(self.releases)

        self.table = QTableWidget(len(self.local_tracks), 3)
        self.table.setHorizontalHeaderLabels(["#", "TÍTULO ACTUAL", "TÍTULO PROPUESTO (EDITABLE)"])
        self.table.setColumnWidth(0, 42)
        self.table.setColumnWidth(1, 330)
        self.table.horizontalHeader().setStretchLastSection(True)
        for index, track in enumerate(self.local_tracks):
            number = track["track_number"] or index + 1
            self.table.setItem(index, 0, QTableWidgetItem(str(number)))
            current = QTableWidgetItem(track["title"])
            current.setFlags(current.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(index, 1, current)
            self.table.setItem(index, 2, QTableWidgetItem(track["title"]))
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        retry = QPushButton("Buscar de nuevo")
        retry.clicked.connect(self.search)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        self.apply_button = QPushButton("Aplicar títulos")
        self.apply_button.setObjectName("primaryButton")
        self.apply_button.clicked.connect(self._apply)
        buttons.addWidget(retry)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(self.apply_button)
        root.addLayout(buttons)
        self.search()

    def _request(self, url: QUrl, callback: object) -> None:
        request = QNetworkRequest(url)
        request.setRawHeader(
            b"User-Agent", f"VinqeloPlayer/{APP_VERSION} (local music player)".encode()
        )
        request.setRawHeader(b"Accept", b"application/json")
        reply = self.network.get(request)
        reply.finished.connect(lambda: callback(reply))

    def search(self) -> None:
        self.releases.clear()
        if not internet_access_allowed():
            self.status.setText(
                "Las búsquedas en internet están desactivadas en Configuración."
            )
            return
        self.status.setText("Buscando ediciones musicales…")
        artist = self.album["artist_name"] or self.album["album_artist"]
        url = QUrl("https://musicbrainz.org/ws/2/release/")
        query = QUrlQuery()
        query.addQueryItem("query", f'release:"{self.album["title"]}" AND artist:"{artist}"')
        query.addQueryItem("fmt", "json")
        query.addQueryItem("limit", "15")
        url.setQuery(query)
        self._request(url, self._search_finished)

    def _search_finished(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise RuntimeError(reply.errorString())
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            releases = data.get("releases", [])
            for release in releases:
                date = str(release.get("date", ""))[:4]
                country = release.get("country", "")
                tracks = release.get("track-count", "?")
                label = f'{release.get("title", "Álbum")} · {date or "s/f"} · {country or "—"} · {tracks} pistas'
                item = QListWidgetItem(label)
                item.setData(256, release.get("id"))
                self.releases.addItem(item)
            self.status.setText(
                "Selecciona la edición que coincida con tu carpeta."
                if releases else "No se encontraron ediciones coincidentes."
            )
            if self.releases.count():
                self.releases.setCurrentRow(0)
        except Exception as exc:
            self.status.setText(f"No se pudo consultar MusicBrainz: {exc}")
        finally:
            reply.deleteLater()

    def _release_selected(self, item: QListWidgetItem | None, _previous: object) -> None:
        if item is None:
            return
        release_id = item.data(256)
        url = QUrl(f"https://musicbrainz.org/ws/2/release/{release_id}")
        query = QUrlQuery()
        query.addQueryItem("inc", "recordings")
        query.addQueryItem("fmt", "json")
        url.setQuery(query)
        self.status.setText("Cargando lista oficial de pistas…")
        self._request(url, self._tracks_finished)

    def _tracks_finished(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                raise RuntimeError(reply.errorString())
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            titles: list[str] = []
            for medium in data.get("media", []):
                for track in medium.get("tracks", []):
                    title = track.get("title") or track.get("recording", {}).get("title")
                    if title:
                        titles.append(str(title))
            for index, track in enumerate(self.local_tracks):
                proposed = titles[index] if index < len(titles) else track["title"]
                self.table.setItem(index, 2, QTableWidgetItem(proposed))
            self.status.setText(
                f"Edición cargada: {len(titles)} pistas oficiales. Revisa la asignación antes de aplicar."
            )
        except Exception as exc:
            self.status.setText(f"No se pudo cargar esa edición: {exc}")
        finally:
            reply.deleteLater()

    def _apply(self) -> None:
        changed = 0
        renamed: dict[str, str] = {}
        try:
            for index, track in enumerate(self.local_tracks):
                cell = self.table.item(index, 2)
                title = cell.text().strip() if cell else ""
                if title and title != track["title"]:
                    old_path = str(track["file_path"])
                    new_path = self.database.update_track_title(old_path, title)
                    renamed[old_path] = new_path
                    changed += 1
        except Exception as exc:
            QMessageBox.warning(self, "No se pudieron aplicar los datos", str(exc))
            return
        self.metadata_applied.emit(renamed)
        QMessageBox.information(self, "Datos actualizados", f"Se actualizaron {changed} títulos.")
        self.accept()
