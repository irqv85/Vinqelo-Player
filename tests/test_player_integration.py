"""Prueba básica del controlador contra una instalación real de VLC."""

from __future__ import annotations

import tempfile
import unittest
import wave
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from library.track_metadata import read_track_details
from player.controller import PlaybackState, PlayerController


def _has_native_vlc() -> bool:
    try:
        import vlc

        return bool(vlc.libvlc_get_version())
    except Exception:
        return False


@unittest.skipUnless(_has_native_vlc(), "VLC nativo no está instalado")
class PlayerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_open_pause_resume_seek_volume_and_stop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            audio_path = Path(temporary_directory) / "silencio.wav"
            with wave.open(str(audio_path), "wb") as audio_file:
                audio_file.setnchannels(1)
                audio_file.setsampwidth(2)
                audio_file.setframerate(44_100)
                audio_file.writeframes(b"\x00\x00" * 22_050)

            controller = PlayerController()
            errors: list[str] = []
            queue_states: list[tuple[list[str], int]] = []
            controller.error_occurred.connect(errors.append)
            controller.queue_changed.connect(
                lambda paths, index: queue_states.append((paths, index))
            )
            try:
                details = read_track_details(audio_path)
                self.assertEqual(details.file_format, "WAV")
                self.assertEqual(details.codec, "PCM")
                self.assertEqual(details.sample_rate_hz, 44_100)
                self.assertEqual(details.channels, 1)
                self.assertIn("44.1 kHz", details.quality_line)
                self.assertTrue(controller.open_file(audio_path))
                self.assertEqual(controller.state, PlaybackState.PLAYING)
                controller.pause()
                self.assertEqual(controller.state, PlaybackState.PAUSED)
                controller.play()
                controller.seek_to(100)
                controller.skip(1)
                controller.set_volume(35)
                controller.stop()
                self.assertEqual(controller.state, PlaybackState.STOPPED)
                second_path = Path(temporary_directory) / "silencio-2.wav"
                second_path.write_bytes(audio_path.read_bytes())
                self.assertTrue(controller.set_queue([audio_path], autoplay=False))
                self.assertEqual(controller.enqueue_files([second_path]), 1)
                self.assertEqual(len(queue_states[-1][0]), 2)
                self.assertEqual(queue_states[-1][1], 0)
                self.assertTrue(controller.play_index(1))
                self.assertEqual(controller.current_file, second_path.resolve())
                controller.previous()
                self.assertEqual(controller.current_file, audio_path.resolve())
                controller.next()
                self.assertEqual(controller.current_file, second_path.resolve())
                self.assertEqual(errors, [])
            finally:
                controller.shutdown()


if __name__ == "__main__":
    unittest.main()
