#!/usr/bin/env python3
"""Generate the spritesheets for the two enemies added in Level 4.

Usage:  python scripts/make_new_actors.py
Writes: Assets/Spritesheet/bat_fly.png      (4 frames, 64x64 each)
        Assets/Spritesheet/spiky_roll.png   (4 frames, 64x64 each)
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

CELL = 64
FRAMES = 4
SS = 4  # supersampling factor, keeps the flat shapes clean


def new_frame():
    return Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))


def ell(d, cx, cy, rx, ry, fill, outline=None, w=3):
    d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS],
              fill=fill, outline=outline, width=w * SS)


def poly(d, pts, fill, outline=None, w=3):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=outline, width=w * SS)


# --------------------------------------------------------------- BAT
BAT_BODY = (108, 76, 168, 255)
BAT_DARK = (58, 40, 92, 255)
BAT_WING = (146, 108, 208, 255)
BAT_EYE = (255, 255, 255, 255)
BAT_PUPIL = (30, 20, 45, 255)
BAT_FANG = (255, 250, 240, 255)


def bat_frame(t):
    """t in 0..1 -> wing flap phase."""
    img = new_frame()
    d = ImageDraw.Draw(img)
    cx, cy = 32, 34
    flap = math.sin(t * math.tau)          # -1 .. 1
    tip_y = cy - 4 - flap * 12             # wing tip travel
    mid_y = cy + 2 - flap * 5

    for s in (-1, 1):                      # left / right wing
        poly(d, [
            (cx + s * 6, cy - 4),
            (cx + s * 17, tip_y),
            (cx + s * 30, tip_y + 4),
            (cx + s * 24, mid_y + 5),
            (cx + s * 20, mid_y + 1),
            (cx + s * 15, mid_y + 8),
            (cx + s * 11, mid_y + 3),
            (cx + s * 7, mid_y + 9),
        ], BAT_WING, BAT_DARK, 2)

    poly(d, [(cx - 11, cy - 9), (cx - 8, cy - 22), (cx - 3, cy - 11)], BAT_BODY, BAT_DARK, 2)
    poly(d, [(cx + 11, cy - 9), (cx + 8, cy - 22), (cx + 3, cy - 11)], BAT_BODY, BAT_DARK, 2)

    ell(d, cx, cy, 13, 14, BAT_BODY, BAT_DARK, 2)

    for s in (-1, 1):
        ell(d, cx + s * 5.5, cy - 3, 4.2, 4.8, BAT_EYE, BAT_DARK, 1)
        ell(d, cx + s * 5.5, cy - 2.5, 1.9, 2.2, BAT_PUPIL)
    poly(d, [(cx - 3.5, cy + 5), (cx - 1.5, cy + 10), (cx - 0.2, cy + 5)], BAT_FANG)
    poly(d, [(cx + 3.5, cy + 5), (cx + 1.5, cy + 10), (cx + 0.2, cy + 5)], BAT_FANG)
    return img


# ------------------------------------------------------------- SPIKY
SPK_BODY = (203, 67, 53, 255)
SPK_DARK = (110, 30, 24, 255)
SPK_SPIKE = (240, 173, 78, 255)
SPK_EYE = (255, 255, 255, 255)


def spiky_frame(t):
    """t in 0..1 -> spike pulse + body squash."""
    img = new_frame()
    d = ImageDraw.Draw(img)
    cx, cy = 32, 36
    pulse = math.sin(t * math.tau)
    r = 15.0
    spike_len = 9 + pulse * 2.5
    spin = t * math.tau / 10.0

    n = 12
    for i in range(n):
        a = spin + i * math.tau / n
        base = 4.0 * math.tau / (n * 8)
        poly(d, [
            (cx + math.cos(a - base) * (r - 1), cy + math.sin(a - base) * (r - 1)),
            (cx + math.cos(a) * (r + spike_len), cy + math.sin(a) * (r + spike_len)),
            (cx + math.cos(a + base) * (r - 1), cy + math.sin(a + base) * (r - 1)),
        ], SPK_SPIKE, SPK_DARK, 1)

    ell(d, cx, cy, r, r - pulse * 1.2, SPK_BODY, SPK_DARK, 2)

    for s in (-1, 1):
        ell(d, cx + s * 5.5, cy - 2, 4.6, 5.2, SPK_EYE, SPK_DARK, 1)
        ell(d, cx + s * 5.5 + 1.3, cy - 1.5, 2.1, 2.4, SPK_DARK)
    # angry brows
    d.line([((cx - 10) * SS, (cy - 8) * SS), ((cx - 2) * SS, (cy - 5) * SS)], SPK_DARK, 3 * SS)
    d.line([((cx + 10) * SS, (cy - 8) * SS), ((cx + 2) * SS, (cy - 5) * SS)], SPK_DARK, 3 * SS)
    # mouth
    d.arc([(cx - 6) * SS, (cy + 3) * SS, (cx + 6) * SS, (cy + 11) * SS], 200, 340, SPK_DARK, 3 * SS)
    return img


def build(name, maker):
    sheet = Image.new("RGBA", (CELL * FRAMES, CELL), (0, 0, 0, 0))
    for i in range(FRAMES):
        f = maker(i / FRAMES).resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(f, (i * CELL, 0))
    out = Path("Assets/Spritesheet") / name
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    build("bat_fly.png", bat_frame)
    build("spiky_roll.png", spiky_frame)
