"""Genera los recursos visuales exigidos por el paquete MSIX."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "icons" / "vinqelo-v.png"
OUTPUT = ROOT / "packaging" / "Assets"


def fitted_canvas(size: tuple[int, int], margin: float = 0.10) -> Image.Image:
    source = Image.open(SOURCE).convert("RGBA")
    width, height = size
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    available = (int(width * (1 - margin * 2)), int(height * (1 - margin * 2)))
    source.thumbnail(available, Image.Resampling.LANCZOS)
    x = (width - source.width) // 2
    y = (height - source.height) // 2
    canvas.alpha_composite(source, (x, y))
    return canvas


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    resources = {
        "StoreLogo.png": (50, 50),
        "Square44x44Logo.png": (44, 44),
        "Square150x150Logo.png": (150, 150),
        "Wide310x150Logo.png": (310, 150),
        "Square310x310Logo.png": (310, 310),
    }
    for name, size in resources.items():
        fitted_canvas(size).save(OUTPUT / name, "PNG", optimize=True)

    for scale, factor in (
        (100, 1.0),
        (125, 1.25),
        (150, 1.5),
        (200, 2.0),
        (400, 4.0),
    ):
        store_size = math.floor(50 * factor + 0.5)
        square_size = math.floor(44 * factor + 0.5)
        fitted_canvas((store_size, store_size)).save(
            OUTPUT / f"StoreLogo.scale-{scale}.png", "PNG", optimize=True
        )
        fitted_canvas((square_size, square_size), 0.06).save(
            OUTPUT / f"Square44x44Logo.scale-{scale}.png",
            "PNG",
            optimize=True,
        )

    for target_size in (
        16, 20, 24, 30, 32, 36, 40, 44, 48, 60, 64, 72, 80, 96, 256
    ):
        fitted_canvas((target_size, target_size), 0.04).save(
            OUTPUT
            / (
                "Square44x44Logo."
                f"targetsize-{target_size}_altform-unplated.png"
            ),
            "PNG",
            optimize=True,
        )

    audio_icon = Image.open(
        ROOT / "assets" / "icons" / "files" / "vinqelo-mp3.png"
    ).convert("RGBA")
    audio_icon.thumbnail((256, 256), Image.Resampling.LANCZOS)
    audio_icon.save(OUTPUT / "AudioFileLogo.png", "PNG", optimize=True)


if __name__ == "__main__":
    main()
