"""Validaciones mínimas de los iconos incluidos en el paquete Store."""

from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "packaging" / "Assets"


class StoreAssetTests(unittest.TestCase):
    def test_primary_logos_have_transparent_corners(self) -> None:
        for name in (
            "StoreLogo.png",
            "Square44x44Logo.png",
            "Square150x150Logo.png",
            "Wide310x150Logo.png",
            "Square310x310Logo.png",
        ):
            with self.subTest(name=name):
                with Image.open(ASSETS / name).convert("RGBA") as image:
                    corners = (
                        image.getpixel((0, 0))[3],
                        image.getpixel((image.width - 1, 0))[3],
                        image.getpixel((0, image.height - 1))[3],
                        image.getpixel(
                            (image.width - 1, image.height - 1)
                        )[3],
                    )
                    self.assertEqual(corners, (0, 0, 0, 0))

    def test_unplated_shell_icons_cover_common_sizes(self) -> None:
        for size in (16, 24, 32, 44, 48, 64, 96, 256):
            path = ASSETS / (
                "Square44x44Logo."
                f"targetsize-{size}_altform-unplated.png"
            )
            with self.subTest(size=size):
                self.assertTrue(path.is_file())
                with Image.open(path) as image:
                    self.assertEqual(image.size, (size, size))

    def test_store_scale_125_uses_rounded_physical_size(self) -> None:
        with Image.open(ASSETS / "StoreLogo.scale-125.png") as image:
            self.assertEqual(image.size, (63, 63))


if __name__ == "__main__":
    unittest.main()
