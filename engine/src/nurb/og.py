"""The card a shared part shows when its link is pasted into a chat or a post.

The share page's own look at link-card size: the part on the stage, and a white panel
with its name, its size and the one thing to do with it. Drawn here rather than on
nurb.app because the engine already has the part and a renderer, and the site has
neither.
"""

import io
import pathlib

BRAND = pathlib.Path(__file__).parent / "brand"
WIDTH, HEIGHT = 1200, 630
STAGE = (0xE5, 0xF0, 0xFB)
GROUND = (0xFF, 0xFF, 0xFF)
EDGE = (0xBD, 0xCE, 0xE2)
LINE = (0xE8, 0xED, 0xF4)
INK = (0x12, 0x18, 0x21)
MUTED = (0x64, 0x70, 0x7F)
ACCENT = (0xFF, 0x52, 0x30)


def _font(size, weight):
    from PIL import ImageFont

    font = ImageFont.truetype(str(BRAND / "InstrumentSans-Variable.ttf"), size)
    font.set_variation_by_name(weight)
    return font


def _lines(draw, text, font, width, most):
    """Words wrapped to `width`, at most `most` lines, the last one cut with an ellipsis."""
    lines = []
    for word in text.split():
        if lines and draw.textlength(f"{lines[-1]} {word}", font=font) <= width:
            lines[-1] = f"{lines[-1]} {word}"
        else:
            lines.append(word)
    if len(lines) > most:
        lines = lines[:most]
        while lines[-1] and draw.textlength(lines[-1] + "…", font=font) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "…"
    return lines


def card(glb, title, size_mm=None):
    """PNG bytes, 1200 by 630."""
    from PIL import Image, ImageDraw

    from . import raster

    out = Image.new("RGB", (WIDTH, HEIGHT), STAGE)
    # Drawn at twice the size and scaled down, so the part's edges stay smooth.
    shot = Image.open(io.BytesIO(raster.render(glb, width=1440, height=1260, view="iso", shadow=raster.SHADOW)))
    shot = shot.convert("RGBA").resize((720, 630), Image.LANCZOS)
    out.paste(shot, (0, 0), shot)

    draw = ImageDraw.Draw(out)
    left, top, right, bottom = 708, 40, 1160, 590
    draw.rounded_rectangle((left, top, right, bottom), radius=16, fill=GROUND, outline=EDGE, width=2)
    inset = left + 40
    room = right - 40 - inset

    lockup = Image.open(BRAND / "lockup.png").convert("RGBA")
    lockup = lockup.resize((132, round(132 * lockup.height / lockup.width)), Image.LANCZOS)
    out.paste(lockup, (inset, top + 40), lockup)

    heading = _font(56, b"SemiBold")
    y = top + 128
    for line in _lines(draw, title, heading, room, 3):
        draw.text((inset, y), line, font=heading, fill=INK)
        y += 62
    if size_mm:
        dims = " × ".join(str(round(n)) for n in size_mm) + " mm"
        draw.text((inset, y + 14), dims, font=_font(26, b"Medium"), fill=MUTED)

    button = (inset, bottom - 40 - 68, right - 40, bottom - 40)
    draw.rounded_rectangle(button, radius=5, fill=ACCENT)
    label, font, tracking = "OPEN IN NURB", _font(22, b"SemiBold"), 3
    span = sum(draw.textlength(c, font=font) for c in label) + tracking * (len(label) - 1)
    x = (button[0] + button[2] - span) / 2
    for c in label:
        draw.text((x, (button[1] + button[3]) / 2), c, font=font, fill=GROUND, anchor="lm")
        x += draw.textlength(c, font=font) + tracking

    data = io.BytesIO()
    out.save(data, "PNG", optimize=True)
    return data.getvalue()
