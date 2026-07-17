"""Vista de la cola real del motor de reproducción."""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from database.manager import DatabaseManager


class QueuePage(QWidget):
    play_index_requested = Signal(int)

    def __init__(self, database: DatabaseManager) -> None:
        super().__init__()
        self.database = database
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
        self.tree.itemDoubleClicked.connect(self._play)
        self.tree.setColumnWidth(0, 110)
        self.tree.setColumnWidth(1, 330)
        self.tree.setColumnWidth(2, 210)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.tree, 1)

    def update_queue(self, paths: object, current_index: int) -> None:
        scroll_position = self.tree.verticalScrollBar().value()
        self.tree.clear()
        if not isinstance(paths, list):
            return
        for index, path in enumerate(paths):
            row = self.database.get_track_by_path(path)
            title = row["title"] if row else path.rsplit("\\", 1)[-1]
            artist = ""
            album = ""
            if row:
                artist = row["track_artist"] if row["is_compilation"] else row["artist_name"]
                album = row["album_title"]
            if index < current_index:
                status = "Reproducida"
            elif index == current_index:
                status = "▶  Sonando"
            elif index == current_index + 1:
                status = "Siguiente"
            else:
                status = "En cola"
            item = QTreeWidgetItem([status, title, artist, album])
            item.setData(0, Qt.ItemDataRole.UserRole, index)
            item.setData(
                0,
                Qt.ItemDataRole.UserRole + 1,
                {"file_path": path},
            )
            self.tree.addTopLevelItem(item)
            if index == current_index:
                font = item.font(1)
                font.setBold(True)
                item.setFont(1, font)
                self.tree.setCurrentItem(item)
        self.tree.verticalScrollBar().setValue(scroll_position)
        QTimer.singleShot(
            0, lambda: self.tree.verticalScrollBar().setValue(scroll_position)
        )

    def _play(self, item: QTreeWidgetItem, _column: int) -> None:
        self.play_index_requested.emit(int(item.data(0, Qt.ItemDataRole.UserRole)))

    def show_root(self) -> None:
        self.tree.verticalScrollBar().setValue(0)
