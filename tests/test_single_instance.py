"""Pruebas del canal que evita abrir varias copias de Vinqelo."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from single_instance import SingleInstanceCoordinator


class SingleInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = (
            QCoreApplication.instance() or QCoreApplication([])
        )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.name = f"VinqeloTest-{uuid.uuid4().hex}"
        self.lock_path = Path(self.temporary.name) / "instance.lock"
        self.primary = SingleInstanceCoordinator(
            self.name, self.lock_path
        )

    def tearDown(self) -> None:
        self.primary.close()
        QCoreApplication.processEvents()
        self.temporary.cleanup()

    def _wait_for(self, predicate: object, timeout: float = 2.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            QCoreApplication.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def _forward_in_parallel(self, paths: list[Path]) -> bool:
        code = """
import sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from single_instance import SingleInstanceCoordinator
application = QCoreApplication([])
coordinator = SingleInstanceCoordinator(sys.argv[1], Path(sys.argv[2]))
is_primary = coordinator.start_or_forward(
    [Path(value) for value in sys.argv[3:]]
)
raise SystemExit(7 if is_primary else 0)
"""
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                code,
                self.name,
                str(self.lock_path),
                *(str(path) for path in paths),
            ],
            cwd=str(Path(__file__).resolve().parents[1]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        while process.poll() is None:
            QCoreApplication.processEvents()
            time.sleep(0.005)
        stdout, stderr = process.communicate()
        self.assertEqual(
            process.returncode,
            0,
            f"stdout={stdout}\nstderr={stderr}",
        )
        return False

    def test_second_instance_forwards_files_and_does_not_continue(self) -> None:
        received: list[list[str]] = []
        self.assertTrue(self.primary.start_or_forward([]))
        self.primary.set_activation_handler(received.append)
        tracks = [
            Path(self.temporary.name) / "Primera canción.mp3",
            Path(self.temporary.name) / "Segunda.flac",
        ]

        self.assertFalse(self._forward_in_parallel(tracks))
        self.assertTrue(self._wait_for(lambda: bool(received)))
        self.assertEqual(
            received,
            [[str(path.resolve()) for path in tracks]],
        )

    def test_plain_second_launch_requests_existing_window(self) -> None:
        received: list[list[str]] = []
        self.assertTrue(self.primary.start_or_forward([]))
        self.primary.set_activation_handler(received.append)

        self.assertFalse(self._forward_in_parallel([]))
        self.assertTrue(self._wait_for(lambda: bool(received)))
        self.assertEqual(received, [[]])

    def test_activation_waits_until_window_handler_is_ready(self) -> None:
        self.assertTrue(self.primary.start_or_forward([]))
        track = Path(self.temporary.name) / "Pendiente.ogg"
        self.assertFalse(self._forward_in_parallel([track]))
        self.assertTrue(
            self._wait_for(lambda: bool(self.primary._pending))
        )
        received: list[list[str]] = []

        self.primary.set_activation_handler(received.append)

        self.assertEqual(received, [[str(track.resolve())]])


if __name__ == "__main__":
    unittest.main()
