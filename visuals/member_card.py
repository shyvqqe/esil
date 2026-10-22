"""Render Esil's avatar-coloured glass profile card with local Pillow code."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import unicodedata
import warnings

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from visuals.profile_palette import extract_profile_theme

WIDTH, HEIGHT = 1200, 600
_FONT_ROOT = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_PANEL_BOX = (100, 78, 1100, 528)


@lru_cache(maxsize=48)
def _font(size: int, bold: bool = False):
    """Prefer a full Cyrillic font; never silently render missing glyph boxes."""
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = (
        _FONT_ROOT / filename,
        Path("/usr/share/fonts/truetype/dejavu") / filename,
        Path("/usr/share/fonts/dejavu") / filename,
        Path("/usr/local/share/fonts") / filename,
        Path("C:/Windows/Fonts") / ("arialbd.ttf" if bold else "arial.ttf"),
        filename,
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    raise RuntimeError("A Cyrillic font is required: add assets/fonts/DejaVuSans.ttf")


@lru_cache(maxsize=4096)
def _supported_character(char: str) -> bool:
    if char.isspace():
        return True
    font = _font(16)
    glyph, missing = font.getmask(char), font.getmask("\uffff")
    return glyph.size != missing.size or bytes(glyph) != bytes(missing)


def _text(value, limit: int = 100) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")[:max(200, limit * 4)])
    # The bundled text font has no colour emoji. Filter unsupported characters
    # so decorated Discord names stay readable instead of showing tofu boxes.
    return " ".join("".join(
        char for char in value
        if not unicodedata.category(char).startswith("C")
        and ord(char) <= 0xFFFF and char not in "\ufe0e\ufe0f"
        and _supported_character(char)
    ).split())[:limit]


def _fit(draw, text: str, max_width: int, size: int, *, bold=False, minimum=13):
    for current_size in range(size, minimum - 1, -1):
        font = _font(current_size, bold)
        if draw.textlength(text, font=font) <= max_width:
            return text, font
    font = _font(minimum, bold)
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text + "…", font


def _integer(value, default=0):
    try:
        return max(0, min(10**18, int(value)))
    except (TypeError, ValueError, OverflowError):
        return default


def _number(value, *, fallback="—") -> str:
    try:
        number = max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return fallback
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f} млрд"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f} млн"
    return f"{number:,}".replace(",", " ")


def _rgb(value, default):
    if isinstance(value, (tuple, list)) and len(value) == 3:
        try:
            return tuple(max(0, min(255, int(channel))) for channel in value)
        except (TypeError, ValueError, OverflowError):
            pass
    return default


def _mix(first, second, ratio):
    return tuple(round(a * (1 - ratio) + b * ratio) for a, b in zip(first, second))


def _background(theme) -> Image.Image:
    top, bottom = theme["background_top"], theme["background_bottom"]
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        draw.line((0, y, WIDTH, y), fill=_mix(top, bottom, y / (HEIGHT - 1)))
    glow = Image.new("RGBA", image.size)
    light = ImageDraw.Draw(glow)
    light.ellipse((-270, -270, 720, 510), fill=(*theme["glow"], 68))
    light.ellipse((580, -300, 1450, 470), fill=(*theme["accent"], 20))
    return Image.alpha_composite(image, glow.filter(ImageFilter.GaussianBlur(110)))


def _glass(image, theme):
    shadow = Image.new("RGBA", image.size)
    ImageDraw.Draw(shadow).rounded_rectangle((105, 104, 1095, 548), radius=52,
                                             fill=(12, 8, 16, 105))
    image = Image.alpha_composite(image, shadow.filter(ImageFilter.GaussianBlur(28)))
    mask = Image.new("L", (WIDTH * 2, HEIGHT * 2))
    ImageDraw.Draw(mask).rounded_rectangle(tuple(v * 2 for v in _PANEL_BOX), radius=104, fill=255)
    mask = mask.resize(image.size, Image.Resampling.LANCZOS)
    panel = Image.new("RGBA", image.size)
    panel_draw = ImageDraw.Draw(panel)
    for y in range(78, 529):
        # A near-opaque tint preserves palette contrast while a small amount
        # of the blurred background creates the glass depth of the reference.
        tint = _mix(theme["panel"], theme["glow"], 0.04 * (528 - y) / 450)
        panel_draw.line((100, y, 1100, y), fill=(*tint, 242))
    # Keep the light on the avatar half; the statistics half stays within the
    # contrast-safe panel shade selected by the palette helper.
    sheen = Image.new("RGBA", image.size)
    ImageDraw.Draw(sheen).ellipse((-60, -170, 540, 430), fill=(*theme["glow"], 48))
    panel = Image.alpha_composite(panel, sheen.filter(ImageFilter.GaussianBlur(85)))
    frost = Image.alpha_composite(image.filter(ImageFilter.GaussianBlur(20)), panel)
    image.paste(frost, (0, 0), mask)
    border = Image.new("RGBA", (1004 * 3, 454 * 3))
    edge = ImageDraw.Draw(border)
    edge.rounded_rectangle((6, 6, 3006, 1356), radius=156,
                           outline=(*theme["text"], 72), width=3)
    image.alpha_composite(border.resize((1004, 454), Image.Resampling.LANCZOS), (98, 76))
    return image


def _avatar(avatar_bytes: bytes | None, name: str, theme, size: int = 294):
    avatar = None
    if avatar_bytes and len(avatar_bytes) <= 8 * 1024 * 1024:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(avatar_bytes)) as source:
                    if source.width * source.height > 20_000_000:
                        raise ValueError("Avatar exceeds pixel limit")
                    source.verify()
                with Image.open(BytesIO(avatar_bytes)) as source:
                    source.seek(0)
                    cropped = ImageOps.fit(ImageOps.exif_transpose(source).convert("RGBA"),
                                           (size, size), method=Image.Resampling.LANCZOS)
                    # Transparent avatar margins belong on the chosen card
                    # colour; converting directly to RGB would turn them black.
                    avatar = Image.new("RGBA", (size, size), (*theme["panel"], 255))
                    avatar.alpha_composite(cropped)
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            avatar = None
    if avatar is None:
        avatar = Image.new("RGB", (size, size), theme["background_bottom"])
        draw = ImageDraw.Draw(avatar)
        draw.ellipse((80, -100, size + 160, size + 30), fill=theme["panel"])
        initials = "".join(part[0] for part in name.split()[:2]).upper() or "E"
        text, font = _fit(draw, initials, size - 40, 90, bold=True, minimum=40)
        draw.text((size / 2, size / 2), text, font=font, fill=theme["text"], anchor="mm")
    mask = Image.new("L", (size * 3, size * 3))
    ImageDraw.Draw(mask).ellipse((0, 0, size * 3 - 1, size * 3 - 1), fill=255)
    avatar.putalpha(mask.resize((size, size), Image.Resampling.LANCZOS))
    return avatar


def _portrait(image, avatar_bytes, name, theme):
    shadow = Image.new("RGBA", image.size)
    ImageDraw.Draw(shadow).ellipse((160, 162, 466, 468), fill=(8, 6, 12, 110))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(17)))
    # Render the slim ring separately at 3x resolution for a smooth outline.
    ring = Image.new("RGBA", (936, 936))
    ring_draw = ImageDraw.Draw(ring)
    ring_draw.ellipse((2, 2, 933, 933), fill=(*theme["muted"], 110))
    ring_draw.ellipse((10, 10, 925, 925), fill=(*theme["text"], 185))
    ring_draw.ellipse((20, 20, 915, 915), fill=(*theme["panel"], 255))
    image.alpha_composite(ring.resize((312, 312), Image.Resampling.LANCZOS), (154, 148))
    image.alpha_composite(_avatar(avatar_bytes, name, theme), (163, 157))


def _progress(image, theme, ratio):
    scale, width, height = 3, 518, 24
    bar = Image.new("RGBA", (width * scale, height * scale))
    draw = ImageDraw.Draw(bar)
    draw.rounded_rectangle((0, 0, width * scale - 1, height * scale - 1), radius=12 * scale,
                           fill=(*theme["text"], 25), outline=(*theme["text"], 100), width=2)
    if ratio > 0:
        fill_width = max(20 * scale, int((width - 4) * scale * ratio))
        draw.rounded_rectangle((2 * scale, 2 * scale, min((width - 2) * scale, fill_width),
                                (height - 2) * scale), radius=10 * scale,
                               fill=(*theme["accent"], 245))
    image.alpha_composite(bar.resize((width, height), Image.Resampling.LANCZOS), (520, 437))


def render_member_card(data: dict, avatar_bytes: bytes | None = None) -> bytes:
    """Return a PNG containing only the provided real profile and XP values.

    This is CPU work for a worker thread. There are no network or database
    requests; colours are measured from the avatar by the local palette helper.
    """
    keys = ("background_top", "background_bottom", "glow", "panel", "text", "muted", "accent")
    supplied = data.get("theme")
    if isinstance(supplied, dict) and all(key in supplied for key in keys):
        # The asynchronous builder already measured the avatar. Do not repeat
        # that CPU work on every render when a prepared palette was supplied.
        fallback = extract_profile_theme(None, fallback_key=str(data.get("user_id", "")))
    else:
        fallback = extract_profile_theme(avatar_bytes, fallback_key=str(data.get("user_id", "")))
    theme = {key: _rgb(supplied.get(key), fallback[key]) if isinstance(supplied, dict)
             else fallback[key] for key in keys}
    image = _glass(_background(theme), theme)
    name = _text(data.get("display_name"), 100) or "Участник"
    username = _text(data.get("username"), 80).lstrip("@")
    guild = _text(data.get("guild_name"), 100) or "Сообщество"
    role = _text(data.get("role_name"), 80)
    level = _integer(data.get("level"))
    xp_into = _integer(data.get("xp_into"))
    xp_required = max(1, _integer(data.get("xp_required"), 1))
    _portrait(image, avatar_bytes, name, theme)
    draw = ImageDraw.Draw(image)

    handle = "@" + username if username else name
    title, font = _fit(draw, handle, 520, 65, bold=True, minimum=31)
    draw.text((518, 145), title, font=font, fill=theme["text"], anchor="lt")
    subtitle = f"{name} // {role or guild}"
    text, font = _fit(draw, subtitle, 518, 28, minimum=18)
    draw.text((522, 222), text, font=font, fill=theme["muted"], anchor="lt")

    user_id = str(data.get("user_id") or "").strip()
    id_text = "ID: " + user_id if user_id.isascii() and user_id.isdecimal() else "ID: —"
    id_text, id_font = _fit(draw, id_text, 472, 20, bold=True, minimum=16)
    chip_width = min(518, int(draw.textlength(id_text, font=id_font)) + 34)
    chip = Image.new("RGBA", image.size)
    ImageDraw.Draw(chip).rounded_rectangle((520, 273, 520 + chip_width, 317), radius=12,
                                          fill=(*theme["background_bottom"], 100),
                                          outline=(*theme["text"], 20), width=1)
    image.alpha_composite(chip)
    draw = ImageDraw.Draw(image)
    draw.text((537, 295), id_text, font=id_font, fill=theme["text"], anchor="lm")

    xp_text = f"{_number(xp_into)} / {_number(xp_required)} XP"
    level_text = f"LVL {_number(level)}"
    level_text, level_font = _fit(draw, level_text, 166, 22, bold=True, minimum=16)
    pill_width = min(194, int(draw.textlength(level_text, font=level_font)) + 30)
    pill_left = 1038 - pill_width
    xp_text, xp_font = _fit(draw, xp_text, pill_left - 538, 26, minimum=18)
    draw.text((520, 404), xp_text, font=xp_font, fill=theme["text"], anchor="lm")
    draw.rounded_rectangle((pill_left, 384, 1038, 423), radius=19, fill=theme["text"])
    draw.text((pill_left + pill_width / 2, 403), level_text, font=level_font,
              fill=theme["panel"], anchor="mm")
    _progress(image, theme, min(1.0, xp_into / xp_required))
    draw.text((1038, 495), "E S I L", font=_font(10), fill=theme["muted"], anchor="rm")

    output = BytesIO()
    image.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()
