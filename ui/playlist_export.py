"""Dialogos y progreso de exportacion de playlists."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QInputDialog, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog, QVBoxLayout, QWidget,
)

from library.playlist_exporter import PlaylistExportWorker
from ui.i18n import translate_text


class TrackSelectionDialog(QDialog):
    """Permite exportar toda la playlist o una selección ordenada."""

    def __init__(self, name: str, rows: list[object], parent: QWidget) -> None:
        super().__init__(parent)
        self.rows = rows
        self._updating = False
        self.setWindowTitle(translate_text("Seleccionar canciones"))
        self.setMinimumSize(560, 460)
        layout = QVBoxLayout(self)
        title = QLabel(f"{translate_text('Exportar')}: {name}")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.select_all = QCheckBox(translate_text("Seleccionar todas"))
        self.select_all.setChecked(True)
        self.select_all.toggled.connect(self._toggle_all)
        layout.addWidget(self.select_all)
        self.list = QListWidget()
        self.list.setObjectName("exportTrackList")
        for index, row in enumerate(rows):
            data = dict(row)
            artist = data.get("track_artist") or data.get("artist_name") or ""
            item = QListWidgetItem(
                f'{index + 1:02d}.  {data.get("title", "Pista")}  —  {artist}'
            )
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list.addItem(item)
        self.list.itemChanged.connect(self._selection_changed)
        layout.addWidget(self.list, 1)
        self.counter = QLabel()
        self.counter.setObjectName("mutedLabel")
        layout.addWidget(self.counter)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(translate_text("Continuar"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(translate_text("Cancelar"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._selection_changed()

    def _toggle_all(self, checked: bool) -> None:
        if self._updating:
            return
        self._updating = True
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.list.count()):
            self.list.item(index).setCheckState(state)
        self._updating = False
        self._selection_changed()

    def _selection_changed(self, _item: QListWidgetItem | None = None) -> None:
        selected = sum(
            self.list.item(index).checkState() == Qt.CheckState.Checked
            for index in range(self.list.count())
        )
        self.counter.setText(
            translate_text(f"{selected} de {len(self.rows)} canciones seleccionadas")
        )
        self._updating = True
        self.select_all.setChecked(bool(self.rows) and selected == len(self.rows))
        self._updating = False
        buttons = self.findChild(QDialogButtonBox)
        if buttons is not None:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(selected > 0)

    def selected_rows(self) -> list[object]:
        return [
            self.rows[int(self.list.item(index).data(Qt.ItemDataRole.UserRole))]
            for index in range(self.list.count())
            if self.list.item(index).checkState() == Qt.CheckState.Checked
        ]


class PlaylistExportController(QObject):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.parent_widget = parent
        self._thread: QThread | None = None
        self._worker: PlaylistExportWorker | None = None
        self._progress: QProgressDialog | None = None

    def start(self, name: str, rows: list[object]) -> None:
        if self._thread is not None:
            QMessageBox.information(
                self.parent_widget,
                translate_text("Exportación"),
                translate_text("Ya hay una exportación en curso."),
            )
            return
        if not rows:
            QMessageBox.information(
                self.parent_widget,
                translate_text("Exportación"),
                translate_text("La lista no contiene pistas."),
            )
            return
        selection = TrackSelectionDialog(name, rows, self.parent_widget)
        if selection.exec() != QDialog.DialogCode.Accepted:
            return
        rows = selection.selected_rows()
        format_options = {
            translate_text("MP3 · 128 kbps"): "mp3",
            translate_text("OGG · 128 kbps equivalente"): "ogg",
            translate_text("WMA · 128 kbps"): "wma",
        }
        output_label, accepted = QInputDialog.getItem(
            self.parent_widget,
            translate_text("Exportar playlist"),
            translate_text("Formato de salida:"),
            list(format_options),
            0,
            False,
        )
        if not accepted:
            return
        destination = QFileDialog.getExistingDirectory(
            self.parent_widget,
            translate_text("Selecciona el directorio de destino"),
        )
        if not destination:
            return
        tracks = [dict(row) for row in rows]
        worker = PlaylistExportWorker(name, tracks, destination, format_options[output_label])
        thread = QThread(self)
        worker.moveToThread(thread)
        progress = QProgressDialog(
            translate_text("Preparando exportación…"),
            translate_text("Cancelar"),
            0,
            len(tracks),
            self.parent_widget,
        )
        progress.setWindowTitle(translate_text("Exportando playlist"))
        progress.setAutoClose(False)
        progress.setMinimumDuration(0)
        thread.started.connect(worker.run)
        worker.progress.connect(
            lambda current, total, title: self._update_progress(current, total, title)
        )
        # Se llama directamente: el worker esta ocupado convirtiendo y su cola
        # de eventos no podria atender una cancelacion hasta terminar.
        progress.canceled.connect(lambda: worker.cancel())
        worker.finished.connect(self._finished)
        worker.failed.connect(self._failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._cleanup)
        self._thread = thread
        self._worker = worker
        self._progress = progress
        progress.show()
        thread.start()

    def _update_progress(self, current: int, total: int, title: str) -> None:
        if self._progress is None:
            return
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        self._progress.setLabelText(
            f"{title}\n{translate_text(f'{current} de {total} pistas')}"
        )

    def _finished(self, folder: str, exported: int, errors: object, cancelled: bool) -> None:
        if self._progress is not None:
            self._progress.close()
        error_list = list(errors or [])
        if cancelled:
            text = (
                f"{translate_text('Exportación cancelada.')} "
                f"{translate_text('Se copiaron')} {translate_text(f'{exported} pistas')} "
                f"{translate_text('en:')}\n{folder}"
            )
        else:
            text = (
                f"{translate_text('Playlist exportada como compilación.')}\n"
                f"{translate_text(f'{exported} pistas')} {translate_text('en:')}\n{folder}"
            )
        if error_list:
            text += (
                f"\n\n{translate_text('No se pudieron exportar')} "
                f"{translate_text(f'{len(error_list)} pistas')}."
            )
        QMessageBox.information(
            self.parent_widget, translate_text("Exportación terminada"), text
        )

    def _failed(self, message: str) -> None:
        if self._progress is not None:
            self._progress.close()
        QMessageBox.warning(
            self.parent_widget, translate_text("No se pudo exportar"), message
        )

    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
        self._progress = None
