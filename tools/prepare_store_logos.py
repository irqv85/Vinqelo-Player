"""Genera el arte de póster y caja de Microsoft Store desde el logo oficial."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LOGO = ROOT / "assets" / "icons" / "vinqelo-logo.png"
OUTPUT = ROOT / "store-assets" / "es-ES"


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return tuple(round(left + (right - left) * amount) for left, right in zip(a, b))


def _background(size: tuple[int, int]) -> Image.Image:
    width, height = size
    top = (5, 15, 35)
    middle = (9, 32, 73)
    bottom = (12, 8, 45)
    image = Image.new("RGBA", size)
    pixels = image.load()
    for y in range(height):
        progress = y / max(1, height - 1)
        if progress < 0.58:
            color = _mix(top, middle, progress / 0.58)
        else:
            color = _mix(middle, bottom, (progress - 0.58) / 0.42)
        for x in range(width):
            side = abs((x / max(1, width - 1)) - 0.5) * 2
            shade = 1.0 - 0.20 * side
            pixels[x, y] = tuple(round(channel * shade) for channel in color) + (255,)

    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    radius = round(min(size) * 0.54)
    center = (width // 2, round(height * 0.42))
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=(18, 104, 255, 120),
    )
    purple_radius = round(radius * 0.72)
    purple_center = (round(width * 0.68), round(height * 0.56))
    draw.ellipse(
        (
            purple_center[0] - purple_radius,
            purple_center[1] - purple_radius,
            purple_center[0] + purple_radius,
            purple_center[1] + purple_radius,
        ),
        fill=(128, 22, 255, 92),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(round(min(size) * 0.16)))
    image.alpha_composite(glow)

    lines = Image.new("RGBA", size, (0, 0, 0, 0))
    line_draw = ImageDraw.Draw(lines)
    for index in range(7):
        baseline = round(height * (0.64 + index * 0.025))
        points = []
        for x in range(-20, width + 21, 20):
            wave = math.sin((x / width) * math.pi * 2.1 + index * 0.65)
            points.append((x, baseline + round(wave * height * (0.010 + index * 0.002))))
        line_draw.line(points, fill=(90, 124, 255, 34 - index * 3), width=max(2, width // 900))
    image.alpha_composite(lines)
    return image


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    )
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _compose(size: tuple[int, int], logo_fraction: float, title_fraction: float) -> Image.Image:
    canvas = _background(size)
    width, height = size
    logo = Image.open(SOURCE_LOGO).convert("RGBA")
    target = round(min(size) * logo_fraction)
    logo.thumbnail((target, target), Image.Resampling.LANCZOS)

    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    logo_x = (width - logo.width) // 2
    logo_y = round(height * 0.43 - logo.height / 2)
    shadow_logo = Image.new("RGBA", logo.size, (35, 23, 143, 180))
    shadow_logo.putalpha(logo.getchannel("A"))
    shadow.alpha_composite(shadow_logo, (logo_x, logo_y + round(height * 0.018)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(min(size) * 0.025)))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(logo, (logo_x, logo_y))

    title = "Vinqelo Player"
    font = _font(round(min(size) * title_fraction))
    draw = ImageDraw.Draw(canvas)
    box = draw.textbbox((0, 0), title, font=font)
    title_width = box[2] - box[0]
    title_y = min(round(height * 0.79), logo_y + logo.height + round(height * 0.055))
    draw.text(
        ((width - title_width) // 2, title_y),
        title,
        font=font,
        fill=(244, 248, 255, 255),
        stroke_width=max(1, min(size) // 850),
        stroke_fill=(18, 43, 94, 210),
    )
    return canvas.convert("RGB")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    poster = _compose((1440, 2160), logo_fraction=0.70, title_fraction=0.075)
    poster.save(OUTPUT / "poster-store-9x16-1440x2160.png", "PNG", optimize=True)
    box = _compose((2160, 2160), logo_fraction=0.58, title_fraction=0.066)
    box.save(OUTPUT / "caja-store-1x1-2160x2160.png", "PNG", optimize=True)


if __name__ == "__main__":
    main()
