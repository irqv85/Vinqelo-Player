"""Instancia única de Vinqelo y entrega local de activaciones externas."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QLockFile, QObject, QStandardPaths
from PySide6.QtNetwork import QLocalServer, QLocalSocket


ActivationHandler = Callable[[list[str]], None]
MAX_MESSAGE_BYTES = 1024 * 1024


def default_instance_name() -> str:
    """Crea un nombre estable y separado para cada usuario de Windows."""
    identity = f"{Path.home().resolve()}|{os.environ.get('USERNAME', '')}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"VinqeloPlayer-{digest}"


def default_lock_path(instance_name: str) -> Path:
    temporary = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.TempLocation
    )
    return Path(temporary) / f"{instance_name}.lock"


class SingleInstanceCoordinator(QObject):
    """Impide procesos duplicados y reenvía archivos a la primera instancia."""

    def __init__(
        self,
        instance_name: str | None = None,
        lock_path: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.instance_name = instance_name or default_instance_name()
        self.lock_path = lock_path or default_lock_path(self.instance_name)
        self._logger = logging.getLogger(__name__)
        self._lock = QLockFile(str(self.lock_path))
        self._server = QLocalServer(self)
        self._server.setSocketOptions(
            QLocalServer.SocketOption.UserAccessOption
        )
        self._server.newConnection.connect(self._accept_connections)
        self._sockets: set[QLocalSocket] = set()
        self._buffers: dict[QLocalSocket, bytearray] = {}
        self._handler: ActivationHandler | None = None
        self._pending: list[list[str]] = []
        self._primary = False

    @property
    def is_primary(self) -> bool:
        return self._primary

    def start_or_forward(self, file_paths: list[Path]) -> bool:
        """Devuelve ``True`` sólo para el proceso que debe continuar."""
        if self._lock.tryLock(0):
            QLocalServer.removeServer(self.instance_name)
            if not self._server.listen(self.instance_name):
                self._lock.unlock()
                raise RuntimeError(
                    "No se pudo iniciar el canal de instancia única: "
                    f"{self._server.errorString()}"
                )
            self._primary = True
            return True

        forwarded = self._forward_to_primary(file_paths)
        if not forwarded:
            self._logger.error(
                "Vinqelo ya está abierto, pero no respondió al canal local"
            )
        return False

    def set_activation_handler(self, handler: ActivationHandler) -> None:
        self._handler = handler
        pending, self._pending = self._pending, []
        for file_paths in pending:
            handler(file_paths)

    def close(self) -> None:
        for socket in tuple(self._sockets):
            socket.abort()
            socket.deleteLater()
        self._sockets.clear()
        self._buffers.clear()
        if self._server.isListening():
            self._server.close()
        if self._primary:
            self._lock.unlock()
            self._primary = False

    def _forward_to_primary(self, file_paths: list[Path]) -> bool:
        message = (
            json.dumps(
                {
                    "files": [
                        str(path.expanduser().resolve())
                        for path in file_paths
                    ]
                },
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            socket = QLocalSocket()
            socket.connectToServer(self.instance_name)
            if socket.waitForConnected(300):
                socket.write(message)
                socket.flush()
                written = socket.waitForBytesWritten(1200)
                socket.disconnectFromServer()
                if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
                    socket.waitForDisconnected(300)
                return written
            socket.abort()
            time.sleep(0.08)
        return False

    def _accept_connections(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            self._sockets.add(socket)
            self._buffers[socket] = bytearray()
            socket.readyRead.connect(
                lambda current=socket: self._read_socket(current)
            )
            socket.disconnected.connect(
                lambda current=socket: self._discard_socket(current)
            )

    def _read_socket(self, socket: QLocalSocket) -> None:
        buffer = self._buffers.get(socket)
        if buffer is None:
            return
        buffer.extend(bytes(socket.readAll()))
        if len(buffer) > MAX_MESSAGE_BYTES:
            self._logger.warning(
                "Se descartó una activación local demasiado grande"
            )
            socket.abort()
            return
        while b"\n" in buffer:
            raw, _separator, remaining = buffer.partition(b"\n")
            buffer[:] = remaining
            self._dispatch_message(raw)

    def _dispatch_message(self, raw: bytes) -> None:
        try:
            payload = json.loads(raw.decode("utf-8"))
            values = payload.get("files", []) if isinstance(payload, dict) else []
            files = [str(value) for value in values if isinstance(value, str)]
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._logger.warning("Se recibió una activación local no válida")
            return
        if self._handler is None:
            self._pending.append(files)
        else:
            self._handler(files)

    def _discard_socket(self, socket: QLocalSocket) -> None:
        self._sockets.discard(socket)
        self._buffers.pop(socket, None)
        socket.deleteLater()

