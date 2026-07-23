from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ui.main_window import MainWindow


class _Controller:
    def __init__(self) -> None:
        self.calls: list[tuple[list[Path], int, bool]] = []

    def set_queue(
        self,
        paths: list[Path],
        *,
        start_index: int,
        autoplay: bool,
    ) -> None:
        self.calls.append((paths, start_index, autoplay))


class _Sidebar:
    def __init__(self) -> None:
        self.now_playing_available = True

    def set_now_playing_available(self, available: bool) -> None:
        self.now_playing_available = available


class _Tray:
    def __init__(self) -> None:
        self.restore_calls = 0

    def restore_window(self) -> None:
        self.restore_calls += 1


class ExternalFileOpenTests(unittest.TestCase):
    def test_windows_open_with_uses_temporary_single_track_queue(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            track = Path(temporary_directory) / "Pista externa.mp3"
            track.touch()
            controller = _Controller()
            window = SimpleNamespace(
                _player_controller=controller,
                _playback_context={"source": "library"},
                sidebar=_Sidebar(),
                _logger=SimpleNamespace(info=lambda *_args: None),
            )

            # No se proporciona _database: la prueba fallaría si esta ruta
            # intentara importar la pista o modificar la biblioteca.
            MainWindow.open_audio_paths(window, [track])

            self.assertEqual(
                controller.calls,
                [([track.resolve()], 0, True)],
            )
            self.assertEqual(window._playback_context, {})
            self.assertFalse(window.sidebar.now_playing_available)

    def test_windows_open_all_keeps_every_track_in_received_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            tracks = [
                root / "01 - Primera.mp3",
                root / "02 - Segunda.flac",
                root / "03 - Tercera.m4a",
            ]
            for track in tracks:
                track.touch()
            unsupported = root / "notas.txt"
            unsupported.touch()
            controller = _Controller()
            window = SimpleNamespace(
                _player_controller=controller,
                _playback_context={"source": "library"},
                sidebar=_Sidebar(),
                _logger=SimpleNamespace(info=lambda *_args: None),
            )

            MainWindow.open_audio_paths(
                window,
                [tracks[0], unsupported, tracks[1], tracks[2]],
            )

            self.assertEqual(
                controller.calls,
                [([track.resolve() for track in tracks], 0, True)],
            )
            self.assertEqual(window._playback_context, {})

    def test_new_windows_activation_reuses_current_player(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            track = Path(temporary_directory) / "Nueva selección.mp3"
            track.touch()
            controller = _Controller()
            tray = _Tray()
            window = SimpleNamespace(
                _player_controller=controller,
                _playback_context={"source": "previous"},
                sidebar=_Sidebar(),
                _logger=SimpleNamespace(info=lambda *_args: None),
                _system_tray=tray,
                open_audio_paths=lambda paths: MainWindow.open_audio_paths(
                    window, paths
                ),
            )

            MainWindow.handle_external_activation(window, [str(track)])

            self.assertEqual(
                controller.calls,
                [([track.resolve()], 0, True)],
            )
            self.assertEqual(tray.restore_calls, 1)

    def test_plain_activation_only_restores_existing_window(self) -> None:
        controller = _Controller()
        tray = _Tray()
        window = SimpleNamespace(
            _player_controller=controller,
            _system_tray=tray,
        )

        MainWindow.handle_external_activation(window, [])

        self.assertEqual(controller.calls, [])
        self.assertEqual(tray.restore_calls, 1)


if __name__ == "__main__":
    unittest.main()
