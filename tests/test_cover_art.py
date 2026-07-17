"""Pruebas puras de consulta y caché de carátulas."""

from __future__ import annotations

import unittest

from library.cover_art import (
    clean_track_title,
    clean_album_search_title,
    cover_cache_path,
    musicbrainz_release_group_query,
    musicbrainz_release_query,
    select_original_album_groups,
)


class CoverArtTests(unittest.TestCase):
    def test_spam_and_repeated_artist_are_removed_from_search_title(self) -> None:
        self.assertEqual(
            clean_track_title("No me platiques más de Luis Miguel", "Luis Miguel"),
            "No me platiques más",
        )
        self.assertEqual(
            clean_track_title("Canción www.descargados.com", "Artista"),
            "Canción",
        )
    def test_musicbrainz_query_uses_album_and_artist(self) -> None:
        self.assertEqual(
            musicbrainz_release_query('Álbum "Azul"', "Artista"),
            'release:"Álbum \\"Azul\\"" AND artist:"Artista"',
        )

    def test_exact_album_search_excludes_compilations(self) -> None:
        query = musicbrainz_release_group_query("Mis Romances", "Luis Miguel")
        self.assertIn('release:"Mis Romances"', query)
        self.assertIn("primarytype:Album", query)
        groups = [
            {
                "id": "compilation",
                "title": "Mis Romances",
                "primary-type": "Album",
                "secondary-types": ["Compilation"],
                "artist-credit": [{"artist": {"name": "Luis Miguel"}}],
            },
            {
                "id": "original",
                "title": "Mis Romances",
                "primary-type": "Album",
                "secondary-types": [],
                "artist-credit": [{"artist": {"name": "Luis Miguel"}}],
            },
        ]
        selected = select_original_album_groups(groups, "Mis Romances", "Luis Miguel")
        self.assertEqual([item["id"] for item in selected], ["original"])

    def test_folder_prefixes_are_removed_only_for_album_search(self) -> None:
        folder_name = "Luis Miguel - 2001 - Mis Romances"
        self.assertEqual(
            clean_album_search_title(folder_name, "Luis Miguel"), "Mis Romances"
        )
        query = musicbrainz_release_group_query(folder_name, "Luis Miguel")
        self.assertIn('release:"Mis Romances"', query)

    def test_cache_path_is_stable_and_case_insensitive(self) -> None:
        first = cover_cache_path("Inolvidable", "José Luis Rodríguez")
        second = cover_cache_path("INOLVIDABLE", "JOSÉ LUIS RODRÍGUEZ")
        self.assertEqual(first, second)
        self.assertEqual(first.suffix, ".img")


if __name__ == "__main__":
    unittest.main()
