"""Pixel avatar: the photo cut out, ordered-dithered into four colours of the
portfolio palette and set on a circle the head pops out of.

Not part of the daily render; run it once when the photo changes.

    pip install pillow
    python -m gen.tools.avatar foto.jpg --frame studio --name avatar
    python -m gen.tools.avatar janela.png --frame window --name avatar-window

Writes avatar/<name>[-night]-{128,512,1024}.png (square; GitHub and most
social networks crop it to a circle, which the composition leaves room for).
Each photo needs its own framing; FRAMES holds the ones used so far.
"""

import argparse
import os
import struct
import zlib

from .portrait import _background

N = 128                      # pixel grid
CIRCLE = (64, 70, 54)        # centre x, centre y, radius, in avatar pixels

# per photo: working width (None keeps the original), photo pixels per avatar
# pixel, photo x to centre on, photo y of the top of the hair and the avatar
# row it lands on, avatar row where the body starts, background thresholds
FRAMES = {
    # studio portrait on a white backdrop
    "studio": {"width": 421, "scale": 3.6, "center": 215, "top": 12, "top_row": 8, "body_row": 86,
               "bg_lum": .78, "bg_sat": .12, "weights": (.2126, .7152, .0722), "gamma": 1.15},
    # by the window: grey curtain and daylight behind, backlit face. The window
    # lights the hair as much as the face, so tone is read mostly from the red
    # channel: warm skin stays bright, neutral hair drops back
    "window": {"width": None, "scale": 2.0, "center": 113, "top": 118, "top_row": 8, "body_row": 88,
               "bg_lum": .34, "bg_sat": .2, "weights": (.85, .15, 0), "gamma": 1.5},
}

THEMES = {
    # background, circle, then the subject ramp from dark to light
    "cream": {"bg": "#E8E4D4", "circle": "#D8B24A", "ramp": ["#0D1A12", "#2E6B44", "#D8B24A", "#E8E4D4"]},
    "night": {"bg": "#0A0F0B", "circle": "#2E6B44", "ramp": ["#17261C", "#1F3B28", "#D8B24A", "#F0CE6A"]},
}

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "avatar")


def rgb_of(hexcol):
    return tuple(int(hexcol[i:i + 2], 16) for i in (1, 3, 5))


def grow(mask, steps):
    """Dilate the background mask so the photo's light fringe around the hair goes with it."""
    h, w = len(mask), len(mask[0])
    for _ in range(steps):
        mask = [[mask[y][x] or (x > 0 and mask[y][x - 1]) or (x < w - 1 and mask[y][x + 1])
                 or (y > 0 and mask[y - 1][x]) or (y < h - 1 and mask[y + 1][x]) for x in range(w)] for y in range(h)]
    return mask


def sample(rgb, bg, fr):
    """Average the photo into the N×N grid: luminance per cell, None where it's background."""
    h, w = len(rgb), len(rgb[0])
    SCALE = fr["scale"]
    wr, wg, wb = fr["weights"]
    x0, y0 = fr["center"] - N / 2 * SCALE, fr["top"] - fr["top_row"] * SCALE
    grid = []
    for r in range(N):
        row = []
        for c in range(N):
            xa, xb = int(x0 + c * SCALE), int(x0 + (c + 1) * SCALE)
            ya, yb = int(y0 + r * SCALE), int(y0 + (r + 1) * SCALE)
            tot = n = cells = 0
            for y in range(ya, yb):
                for x in range(xa, xb):
                    cells += 1
                    if 0 <= x < w and 0 <= y < h and not bg[y][x]:
                        pr, pg, pb = rgb[y][x]
                        tot += (wr * pr + wg * pg + wb * pb) / 255
                        n += 1
            row.append(tot / n if cells and n * 2 > cells else None)
        grid.append(row)
    return grid


def build(rgb, fr, theme="cream", k=0.9, snap=2.2):
    gamma = fr["gamma"]
    lum = [[(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b in row] for row in rgb]
    sat = [[(max(p) - min(p)) / 255 for p in row] for row in rgb]
    bg = _background(lum, sat, len(rgb[0]), len(rgb), fr["bg_lum"], fr["bg_sat"])
    grid = sample(rgb, grow(bg, 2), fr)
    BODY = fr["body_row"]

    # local contrast so eyes, glasses and beard survive the four colours
    tone = [[None] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            v = grid[r][c]
            if v is None:
                continue
            near = [grid[rr][cc] for rr in range(r - 3, r + 4) for cc in range(c - 3, c + 4)
                    if 0 <= rr < N and 0 <= cc < N and grid[rr][cc] is not None]
            tone[r][c] = v + k * (v - sum(near) / len(near))
    vals = sorted(v for row in tone for v in row if v is not None)
    lo, hi = vals[int(len(vals) * .03)], vals[int(len(vals) * .985)]

    t = THEMES[theme]
    bgc, circle, ramp = rgb_of(t["bg"]), rgb_of(t["circle"]), [rgb_of(x) for x in t["ramp"]]
    ccx, ccy, cr = CIRCLE
    px = []
    for r in range(N):
        row = []
        for c in range(N):
            threshold = (BAYER[r % 4][c % 4] + .5) / 16
            d2 = (c + .5 - ccx) ** 2 + (r + .5 - ccy) ** 2
            inside = d2 <= cr * cr
            v = tone[r][c]
            # the body is clipped by the circle; the head may rise above it
            if v is not None and (inside or r < ccy):
                x = min(1, max(0, (v - lo) / (hi - lo)))
                # fade the body toward the dark end so the face carries the image
                body = min(1.0, max(0.0, (r - BODY) / (N - BODY)))
                x = max(0.0, x - .45 * body * body * (3 - 2 * body)) ** gamma * (len(ramp) - 1)
                i = min(int(x), len(ramp) - 2)
                # squeeze each band so most cells land on a flat colour and only
                # the transitions get dithered, like a two-colour print
                f = min(1, max(0, (x - i - .5) * snap + .5))
                row.append(ramp[i + (f > threshold)])
            elif inside:
                # a light dither toward the rim, like a printed halftone
                edge = max(0.0, (d2 ** .5 - cr * .8) / (cr * .2))
                row.append(bgc if edge * .3 > threshold else circle)
            else:
                row.append(bgc)
        px.append(row)
    return px


def write_png(path, px, scale):
    n = len(px) * scale
    raw = bytearray()
    for row in px:
        line = b"\x00" + b"".join(bytes(p) * scale for p in row)
        raw += line * scale
    chunk = lambda tag, data: struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    print(f"wrote {path}")


def save(rgb, frame="studio", name="avatar"):
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        px = build(rgb, FRAMES[frame], theme)
        suffix = "" if theme == "cream" else f"-{theme}"
        for size in (128, 512, 1024):
            write_png(os.path.join(OUT, f"{name}{suffix}-{size}.png"), px, size // N)


def main():
    from PIL import Image  # only the tools need Pillow

    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--frame", choices=sorted(FRAMES), default="studio")
    ap.add_argument("--name", default="avatar")
    args = ap.parse_args()
    img = Image.open(args.photo).convert("RGB")
    width = FRAMES[args.frame]["width"]
    if width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    p = img.load()
    save([[p[x, y] for x in range(img.width)] for y in range(img.height)], args.frame, args.name)


if __name__ == "__main__":
    main()
