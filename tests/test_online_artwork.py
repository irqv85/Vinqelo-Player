"""Filtrado de resultados del catálogo musical para imágenes manuales."""

from __future__ import annotations

import unittest

from ui.online_artwork_dialog import deezer_artwork_candidates


class OnlineArtworkTests(unittest.TestCase):
    def test_album_candidates_are_music_results_from_expected_artist(self) -> None:
        payload = {
            "data": [
                {
                    "title": "Mis Romances",
                    "cover_xl": "https://music.example/mis-romances.jpg",
                    "artist": {"name": "Luis Miguel"},
                },
                {
                    "title": "Otro álbum",
                    "cover_xl": "https://music.example/other.jpg",
                    "artist": {"name": "Otro cantante"},
                },
            ]
        }
        self.assertEqual(
            deezer_artwork_candidates(
                payload, kind="album", expected_artist="Luis Miguel"
            ),
            [("Mis Romances · Luis Miguel", "https://music.example/mis-romances.jpg")],
        )

    def test_artist_candidates_exclude_unrelated_names_and_duplicates(self) -> None:
        payload = {
            "data": [
                {"name": "Aventura", "picture_xl": "https://music.example/a.jpg"},
                {"name": "Aventura", "picture_xl": "https://music.example/a.jpg"},
                {"name": "Roberto Carlos", "picture_xl": "https://music.example/r.jpg"},
            ]
        }
        self.assertEqual(
            deezer_artwork_candidates(payload, kind="artist", expected_artist="Aventura"),
            [("Aventura", "https://music.example/a.jpg")],
        )


if __name__ == "__main__":
    unittest.main()
