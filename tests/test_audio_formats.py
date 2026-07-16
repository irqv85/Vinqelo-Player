"""Pruebas de formatos de audio admitidos."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from library.audio_formats import is_supported_audio


class AudioFormatTests(unittest.TestCase):
    def test_supported_extensions_are_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            audio_file = Path(temporary_directory) / "pista.FLAC"
            audio_file.touch()
            self.assertTrue(is_supported_audio(audio_file))

    def test_unknown_extension_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            text_file = Path(temporary_directory) / "notas.txt"
            text_file.touch()
            self.assertFalse(is_supported_audio(text_file))


if __name__ == "__main__":
    unittest.main()
