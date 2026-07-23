"""Vista diferida de la cola real del motor de reproducción."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database.manager import DatabaseManager
from ui.i18n import translate_text
from ui.pages.collection_pages import connect_track_click


class QueuePage(QWidget):
    """Muestra una ventana de la cola sin bloquear bibliotecas grandes."""

    play_index_requested = Signal(int)
    MAX_VISIBLE_ROWS = 400
    PREVIOUS_ROWS = 20

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
        self._paths: list[str] = []
        self._current_index = -1
        self._rendered_items: dict[int, QTreeWidgetItem] = {}
        self._render_scheduled = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(6)
        title = QLabel("Cola de reproducción")
        title.setObjectName("pageTitle")
        subtitle = QLabel("La pista actual y todo lo que sonará después.")
        subtitle.setObjectName("pageSubtitle")
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ESTADO", "TÍTULO", "ARTISTA", "ÁLBUM"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        connect_track_click(self.tree, self._play)
        self.tree.setColumnWidth(0, 110)
        self.tree.setColumnWidth(1, 330)
        self.tree.setColumnWidth(2, 210)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.tree, 1)

    def update_queue(self, paths: object, current_index: int) -> None:
        if not isinstance(paths, list):
            return
        new_paths = [str(path) for path in paths]
        old_index = self._current_index
        same_queue = new_paths == self._paths
        self._paths = new_paths
        self._current_index = int(current_index)

        # La página suele estar oculta. Guardar el estado es suficiente hasta
        # que el usuario la abra.
        if not self.isVisible():
            return
        if same_queue and self._current_index in self._rendered_items:
            self._update_statuses(old_index, self._current_index)
            return
        self._schedule_render()

    def _schedule_render(self) -> None:
        if self._render_scheduled:
            return
        self._render_scheduled = True
        QTimer.singleShot(0, self._render_pending)

    def _render_pending(self) -> None:
        self._render_scheduled = False
        if not self.isVisible():
            return
        self.tree.setUpdatesEnabled(False)
        try:
            self.tree.clear()
            self._rendered_items.clear()
            if not self._paths:
                return

            start = max(0, self._current_index - self.PREVIOUS_ROWS)
            end = min(len(self._paths), start + self.MAX_VISIBLE_ROWS)
            visible_paths = self._paths[start:end]
            rows = self.database.get_tracks_by_paths(visible_paths)
            items: list[QTreeWidgetItem] = []

            if start:
                summary = QTreeWidgetItem([
                    "…", translate_text(f"{start} pistas anteriores"), "", ""
                ])
                summary.setFlags(Qt.ItemFlag.NoItemFlags)
                items.append(summary)

            for index in range(start, end):
                path = self._paths[index]
                row = rows.get(path)
                title = row["title"] if row else path.rsplit("\\", 1)[-1]
                artist = ""
                album = ""
                if row:
                    artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
                    album = row["album_title"]
                item = QTreeWidgetItem([
                    self._status(index), str(title), str(artist or ""), str(album or "")
                ])
                item.setData(0, Qt.ItemDataRole.UserRole, index)
                item.setData(0, Qt.ItemDataRole.UserRole + 1, {"file_path": path})
                self._rendered_items[index] = item
                items.append(item)

            remaining = len(self._paths) - end
            if remaining:
                summary = QTreeWidgetItem([
                    "…", translate_text(f"{remaining} pistas más"), "", ""
                ])
                summary.setFlags(Qt.ItemFlag.NoItemFlags)
                items.append(summary)

            self.tree.addTopLevelItems(items)
            self._emphasize_current()
        finally:
            self.tree.setUpdatesEnabled(True)

    def _status(self, index: int) -> str:
        if index < self._current_index:
            return translate_text("Reproducida")
        if index == self._current_index:
            return translate_text("▶  Sonando")
        if index == self._current_index + 1:
            return translate_text("Siguiente")
        return translate_text("En cola")

    def _update_statuses(self, old_index: int, new_index: int) -> None:
        affected = {old_index - 1, old_index, old_index + 1, new_index - 1, new_index, new_index + 1}
        for index in affected:
            item = self._rendered_items.get(index)
            if item is not None:
                item.setText(0, self._status(index))
                font = item.font(1)
                font.setBold(index == new_index)
                item.setFont(1, font)
        self._emphasize_current()

    def _emphasize_current(self) -> None:
        item = self._rendered_items.get(self._current_index)
        if item is None:
            return
        font = item.font(1)
        font.setBold(True)
        item.setFont(1, font)
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(
            item, QAbstractItemView.ScrollHint.PositionAtCenter
        )

    def _play(self, item: QTreeWidgetItem, _column: int) -> None:
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if index is not None:
            self.play_index_requested.emit(int(index))

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._schedule_render()

    def show_root(self) -> None:
        self._schedule_render()
        self.tree.verticalScrollBar().setValue(0)
