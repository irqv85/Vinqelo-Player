"""Normaliza las capturas y recursos promocionales para Microsoft Store."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "store-assets" / "es-ES"
SCREENSHOT_NAMES = (
    "01-biblioteca.png",
    "02-artistas.png",
    "03-albumes.png",
    "04-carpetas.png",
)
BACKGROUND = (7, 16, 32, 255)


def fit_exact(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    scale = min(width / source.width, height / source.height)
    resized = source.resize(
        (round(source.width * scale), round(source.height * scale)),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", size, BACKGROUND)
    canvas.alpha_composite(
        resized,
        ((width - resized.width) // 2, (height - resized.height) // 2),
    )
    return canvas


def fit_transparent(source: Image.Image, size: tuple[int, int], padding: int) -> Image.Image:
    """Centra un logotipo conservando transparencia y una zona segura."""
    width, height = size
    available = (width - padding * 2, height - padding * 2)
    scale = min(available[0] / source.width, available[1] / source.height)
    resized = source.resize(
        (round(source.width * scale), round(source.height * scale)),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.alpha_composite(
        resized,
        ((width - resized.width) // 2, (height - resized.height) // 2),
    )
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero-source", type=Path, required=True)
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)

    hero = Image.open(args.hero_source).convert("RGBA")
    fit_exact(hero, (1920, 1080)).save(
        OUTPUT / "hero-1920x1080.png", "PNG", optimize=True
    )

    logo = Image.open(ROOT / "assets" / "icons" / "vinqelo-logo.png").convert("RGBA")
    fit_transparent(logo, (300, 300), padding=24).save(
        OUTPUT / "icono-tienda-300x300.png", "PNG", optimize=True
    )

    for name in SCREENSHOT_NAMES:
        path = OUTPUT / name
        screenshot = Image.open(path).convert("RGBA")
        fit_exact(screenshot, (1920, 1080)).save(path, "PNG", optimize=True)


if __name__ == "__main__":
    main()
