"""Genera los recursos visuales exigidos por el paquete MSIX."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "icons" / "vinqelo-logo.png"
OUTPUT = ROOT / "packaging" / "Assets"
BACKGROUND = (11, 20, 36, 255)


def fitted_canvas(size: tuple[int, int], margin: float = 0.10) -> Image.Image:
    source = Image.open(SOURCE).convert("RGBA")
    width, height = size
    canvas = Image.new("RGBA", size, BACKGROUND)
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

    audio_icon = Image.open(
        ROOT / "assets" / "icons" / "files" / "vinqelo-mp3.png"
    ).convert("RGBA")
    audio_icon.thumbnail((256, 256), Image.Resampling.LANCZOS)
    audio_icon.save(OUTPUT / "AudioFileLogo.png", "PNG", optimize=True)


if __name__ == "__main__":
    main()
