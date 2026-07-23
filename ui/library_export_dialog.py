"""Selección y control de una exportación completa de biblioteca."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from library.library_exporter import (
    LibraryExportWorker,
    build_library_relative_path,
    build_playlist_relative_path,
)
from ui.i18n import translate_text
from ui.export_progress import ExportProgressDialog


class LibraryExportDialog(QDialog):
    def __init__(self, database: DatabaseManager, parent: QWidget) -> None:
        super().__init__(parent)
        self.database = database
        self._updating = False
        self.setWindowTitle(translate_text("Exportar biblioteca"))
        self.setMinimumSize(680, 560)
        root = QVBoxLayout(self)
        title = QLabel(translate_text("Exportar biblioteca"))
        title.setObjectName("pageTitle")
        note = QLabel(
            translate_text(
                "Selecciona las carpetas y subcarpetas que deseas convertir."
            )
        )
        note.setObjectName("pageSubtitle")
        root.addWidget(title)
        root.addWidget(note)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [translate_text("CARPETA"), translate_text("PISTAS")]
        )
        self.tree.setColumnWidth(0, 500)
        self.tree.itemChanged.connect(self._item_changed)
        root.addWidget(self.tree, 1)
        self._populate()

        options = QHBoxLayout()
        options.addWidget(QLabel(translate_text("Formato de salida:")))
        self.output_format = QComboBox()
        self.output_format.addItem(
            translate_text("MP3 · hasta 128 kbps"), "mp3"
        )
        self.output_format.addItem(
            translate_text("WMA · hasta 160 kbps"), "wma"
        )
        options.addWidget(self.output_format)
        self.normalize = QCheckBox(
            translate_text("Normalizar al pico seguro sin distorsión")
        )
        self.normalize.setChecked(True)
        options.addWidget(self.normalize)
        options.addStretch(1)
        root.addLayout(options)
        destination_row = QHBoxLayout()
        destination_row.addWidget(QLabel(translate_text("Destino:")))
        self.destination = QComboBox()
        removable = removable_drives()
        for drive in removable:
            self.destination.addItem(
                f'{translate_text("Unidad extraíble")} · {drive}', drive
            )
        self.destination.addItem(
            translate_text("Elegir otro directorio…"), ""
        )
        destination_row.addWidget(self.destination, 1)
        self.sync = QCheckBox(
            translate_text("Sincronizar: copiar solo archivos nuevos o modificados")
        )
        self.sync.setChecked(True)
        destination_row.addWidget(self.sync)
        root.addLayout(destination_row)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            translate_text("Continuar")
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            translate_text("Cancelar")
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _populate(self) -> None:
        self._updating = True
        for root in self.database.get_roots():
            artists_data: list[tuple[object, list[object]]] = []
            root_total = 0
            for artist in self.database.get_artists_for_root(int(root["id"])):
                albums = list(
                    self.database.get_albums_for_artist(int(artist["id"]))
                )
                if not albums:
                    continue
                artist_total = sum(int(album["track_count"] or 0) for album in albums)
                root_total += artist_total
                artists_data.append((artist, albums))
            if not artists_data:
                continue
            root_item = self._node(
                Path(root["folder_path"]).name,
                root_total,
                ("root", int(root["id"])),
            )
            self.tree.addTopLevelItem(root_item)
            for artist, albums in artists_data:
                artist_item = self._node(
                    Path(artist["folder_path"]).name,
                    sum(int(album["track_count"] or 0) for album in albums),
                    ("artist", int(artist["id"])),
                )
                root_item.addChild(artist_item)
                for album in albums:
                    artist_item.addChild(
                        self._node(
                            Path(album["folder_path"]).name,
                            int(album["track_count"] or 0),
                            ("album", int(album["id"])),
                        )
                    )
            root_item.setExpanded(True)

        playlists = self.database.get_playlists()
        playlists_group = self._node(
            translate_text("Listas de reproducción"),
            sum(int(playlist["track_count"] or 0) for playlist in playlists),
            ("group", "playlists"),
            checked=False,
        )
        self.tree.addTopLevelItem(playlists_group)
        for playlist in playlists:
            playlists_group.addChild(
                self._node(
                    str(playlist["name"]),
                    int(playlist["track_count"] or 0),
                    ("playlist", int(playlist["id"]), str(playlist["name"])),
                    checked=False,
                )
            )

        global_tracks = self.database.get_smart_tracks_global()
        new_tracks = self.database.get_smart_tracks_new()
        smart_items: list[tuple[str, str, int, int | None]] = [
            ("smart_global", translate_text("Global · Más escuchadas"), len(global_tracks), None),
            ("smart_new", translate_text("New · Últimos 30 días"), len(new_tracks), None),
        ]
        for artist in self.database.get_smart_playlist_artists():
            smart_items.append(
                (
                    "smart_artist",
                    str(artist["name"]),
                    int(artist["track_count"] or 0),
                    int(artist["id"]),
                )
            )
        smart_group = self._node(
            translate_text("Listas inteligentes"),
            sum(item[2] for item in smart_items),
            ("group", "smart"),
            checked=False,
        )
        self.tree.addTopLevelItem(smart_group)
        for kind, name, count, value in smart_items:
            smart_group.addChild(
                self._node(
                    name,
                    count,
                    (kind, value or 0, name),
                    checked=False,
                )
            )
        self._updating = False

    @staticmethod
    def _node(
        name: str,
        count: int,
        data: tuple[object, ...],
        *,
        checked: bool = True,
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([name, str(count)])
        item.setData(0, Qt.ItemDataRole.UserRole, data)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(
            0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )
        return item

    def _item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating or column != 0:
            return
        self._updating = True
        state = item.checkState(0)
        self._set_descendants_state(item, state)
        parent = item.parent()
        while parent is not None:
            checked = [
                parent.child(index).checkState(0)
                for index in range(parent.childCount())
            ]
            parent.setCheckState(
                0,
                checked[0] if checked and len(set(checked)) == 1
                else Qt.CheckState.PartiallyChecked,
            )
            parent = parent.parent()
        self._updating = False

    @classmethod
    def _set_descendants_state(
        cls, item: QTreeWidgetItem, state: Qt.CheckState
    ) -> None:
        """Propaga la selección hasta los álbumes y no sólo al primer nivel."""
        for index in range(item.childCount()):
            child = item.child(index)
            child.setCheckState(0, state)
            cls._set_descendants_state(child, state)

    def selected_sources(self) -> list[tuple[object, ...]]:
        result: list[tuple[object, ...]] = []
        iterator = self.tree.invisibleRootItem()

        def visit(item: QTreeWidgetItem) -> None:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if (
                data
                and data[0] in {
                    "album", "playlist", "smart_global",
                    "smart_new", "smart_artist",
                }
                and item.checkState(0) == Qt.CheckState.Checked
            ):
                result.append(tuple(data))
            for index in range(item.childCount()):
                visit(item.child(index))

        for index in range(iterator.childCount()):
            visit(iterator.child(index))
        return result


class LibraryExportController(QObject):
    def __init__(self, database: DatabaseManager, parent: QWidget) -> None:
        super().__init__(parent)
        self.database = database
        self.parent_widget = parent
        self._thread: QThread | None = None
        self._worker: LibraryExportWorker | None = None
        self._progress: ExportProgressDialog | None = None

    def start(self) -> None:
        if self._thread is not None:
            QMessageBox.information(
                self.parent_widget,
                translate_text("Exportación"),
                translate_text("Ya hay una exportación en curso."),
            )
            return
        dialog = LibraryExportDialog(self.database, self.parent_widget)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        sources = dialog.selected_sources()
        prepared: list[dict[str, object]] = []
        album_ids = [
            int(source[1]) for source in sources if source[0] == "album"
        ]
        for row in self.database.get_tracks_for_export(album_ids):
            data = dict(row)
            data["relative_path"] = str(build_library_relative_path(data))
            prepared.append(data)

        for source in sources:
            kind = str(source[0])
            if kind == "playlist":
                rows = self.database.get_playlist_tracks(int(source[1]))
                name = str(source[2])
                is_smart = False
            elif kind == "smart_global":
                rows = self.database.get_smart_tracks_global()
                name = str(source[2])
                is_smart = True
            elif kind == "smart_new":
                rows = self.database.get_smart_tracks_new()
                name = str(source[2])
                is_smart = True
            elif kind == "smart_artist":
                rows = self.database.get_smart_tracks_for_artist(int(source[1]))
                name = str(source[2])
                is_smart = True
            else:
                continue
            for position, row in enumerate(rows, start=1):
                data = dict(row)
                data["relative_path"] = str(
                    build_playlist_relative_path(
                        name, position, data, smart=is_smart
                    )
                )
                prepared.append(data)

        if not prepared:
            QMessageBox.information(
                self.parent_widget,
                translate_text("Exportación"),
                translate_text("La selección no contiene pistas."),
            )
            return
        destination = str(dialog.destination.currentData() or "")
        if not destination:
            destination = QFileDialog.getExistingDirectory(
                self.parent_widget,
                translate_text("Selecciona el directorio de destino"),
            )
        if not destination:
            return
        worker = LibraryExportWorker(
            prepared,
            destination,
            str(dialog.output_format.currentData()),
            dialog.normalize.isChecked(),
            dialog.sync.isChecked(),
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        progress = ExportProgressDialog(
            translate_text("Preparando exportación…"),
            translate_text("Cancelar"),
            0,
            len(prepared),
            self.parent_widget,
        )
        progress.setWindowTitle(translate_text("Exportar biblioteca"))
        progress.setMinimumDuration(0)
        thread.started.connect(worker.run)
        worker.progress.connect(self._update_progress)
        progress.canceled.connect(lambda: worker.cancel())
        worker.finished.connect(self._finished)
        worker.failed.connect(self._failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(self._cleanup)
        self._thread, self._worker, self._progress = thread, worker, progress
        progress.show()
        thread.start(QThread.Priority.LowPriority)

    def _update_progress(self, current: int, total: int, title: str) -> None:
        if self._progress is not None:
            self._progress.setMaximum(total)
            self._progress.setValue(current)
            self._progress.setLabelText(
                f"{title}\n{translate_text(f'{current} de {total} pistas')}"
            )

    def _finished(
        self,
        folder: str,
        exported: int,
        errors: object,
        cancelled: bool,
        skipped: int,
    ) -> None:
        message = (
            translate_text("Exportación cancelada.")
            if cancelled else translate_text("Exportación terminada")
        )
        message += f"\n{exported} pistas\n{folder}"
        if skipped:
            message += (
                f"\n{skipped} "
                f'{translate_text("archivos ya sincronizados")}'
            )
        if errors:
            message += f"\n\n{len(list(errors))} archivo(s) no pudieron exportarse."
        title = translate_text("Exportación")
        minimized = bool(
            self._progress
            and self._progress.finish(
                title,
                message,
                success=not cancelled and not bool(errors),
            )
        )
        if not minimized:
            QMessageBox.information(self.parent_widget, title, message)

    def _failed(self, message: str) -> None:
        title = translate_text("No se pudo exportar")
        minimized = bool(
            self._progress
            and self._progress.finish(title, message, success=False)
        )
        if not minimized:
            QMessageBox.warning(self.parent_widget, title, message)

    def _cleanup(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._thread = self._worker = self._progress = None


def removable_drives() -> list[str]:
    """Lista unidades extraíbles de Windows sin ejecutar procesos externos."""
    if os.name != "nt":
        return []
    drives: list[str] = []
    mask = int(ctypes.windll.kernel32.GetLogicalDrives())
    for index in range(26):
        if not mask & (1 << index):
            continue
        root = f"{chr(65 + index)}:\\"
        if int(ctypes.windll.kernel32.GetDriveTypeW(root)) == 2:
            drives.append(root)
    return drives
