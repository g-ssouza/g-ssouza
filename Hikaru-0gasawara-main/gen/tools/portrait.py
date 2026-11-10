"""Turns a photo into the coloured ASCII portrait used by the fetch panel.

Not part of the daily render: run it once when the photo changes.

    pip install pillow
    python -m gen.tools.portrait foto.jpg --crop 190 0 750 920

Steps: drop the studio background (light, unsaturated pixels connected to the
top/left/right edges), average the photo into character cells, boost local
contrast so glasses, eyes and beard survive, pick a character by brightness
and keep the cell's own colour, nudged toward the portfolio palette. Colours
are quantised so the SVG stays small. Output: gen/data/portrait.json.
"""

import argparse
import json
import os
import random
from collections import deque

RAMP = " .:-=+*#%@"
OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portrait.json")
# luminance → palette: jade-grey shadows, cream lights, gold highlights
TINT = [(0.0, (0x26, 0x35, 0x2A)), (0.5, (0x8B, 0x96, 0x8A)), (0.8, (0xE8, 0xE4, 0xD4)), (1.0, (0xF0, 0xCE, 0x6A))]


def _background(lum, sat, w, h, lum_min=0.78, sat_max=0.12):
    bg = [[False] * w for _ in range(h)]
    q = deque([(x, 0) for x in range(w)] + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)])
    while q:
        x, y = q.popleft()
        if bg[y][x] or not (lum[y][x] > lum_min and sat[y][x] < sat_max):
            continue
        bg[y][x] = True
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx]:
                q.append((nx, ny))
    return bg


def _tint(rgb, t):
    lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    for (a, ca), (b, cb) in zip(TINT, TINT[1:]):
        if lum <= b:
            f = (lum - a) / (b - a)
            pal = [(ca[i] + (cb[i] - ca[i]) * f) / 255 for i in range(3)]
            break
    return [(1 - t) * x + t * y for x, y in zip(rgb, pal)]


def _quantise(colors, k, seed=7):
    """Plain k-means in RGB; returns (palette, index per colour)."""
    rnd = random.Random(seed)
    centers = rnd.sample(colors, k)
    for _ in range(12):
        groups = [[] for _ in range(k)]
        idx = []
        for c in colors:
            j = min(range(k), key=lambda i: sum((c[n] - centers[i][n]) ** 2 for n in range(3)))
            groups[j].append(c)
            idx.append(j)
        centers = [[sum(c[n] for c in g) / len(g) for n in range(3)] if g else centers[i]
                   for i, g in enumerate(groups)]
    hexes = ["#%02x%02x%02x" % tuple(round(min(1, max(0, v)) * 255) for v in c) for c in centers]
    return hexes, idx


def build(rgb, crop, cols, aspect=2.0, k=1.2, reach=2, lo=0.08, hi=0.85, gamma=0.8,
          lift=0.55, floor=0.15, tint=0.35, ncolors=20):
    """rgb: rows of (r, g, b). crop: (x0, y0, x1, y1) in those pixels."""
    h, w = len(rgb), len(rgb[0])
    lum = [[(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b in row] for row in rgb]
    sat = [[(max(p) - min(p)) / 255 for p in row] for row in rgb]
    bg = _background(lum, sat, w, h)

    x0, y0, x1, y1 = crop
    cw = (x1 - x0) / cols
    ch = cw * aspect
    rows = int((y1 - y0) / ch)
    cells = []
    for r in range(rows):
        line = []
        for c in range(cols):
            xa, xb = int(x0 + c * cw), max(int(x0 + (c + 1) * cw), int(x0 + c * cw) + 1)
            ya, yb = int(y0 + r * ch), max(int(y0 + (r + 1) * ch), int(y0 + r * ch) + 1)
            acc = [0.0, 0.0, 0.0, 0.0]
            n = nb = 0
            for y in range(ya, min(yb, h)):
                for x in range(xa, min(xb, w)):
                    if bg[y][x]:
                        nb += 1
                        continue
                    pr, pg, pb = rgb[y][x]
                    acc[0] += pr; acc[1] += pg; acc[2] += pb; acc[3] += lum[y][x]
                    n += 1
            line.append(None if n <= nb else [v / n for v in acc])
        cells.append(line)

    chars, colors, where = [], [], []
    for r, line in enumerate(cells):
        s = ""
        for c, cell in enumerate(line):
            if cell is None:
                s += " "
                continue
            near = [cells[rr][cc][3] for rr in range(r - reach, r + reach + 1)
                    for cc in range(c - 2 * reach, c + 2 * reach + 1)
                    if 0 <= rr < rows and 0 <= cc < cols and cells[rr][cc]]
            v = cell[3] + k * (cell[3] - sum(near) / len(near))
            v = min(1, max(0, (v - lo) / (hi - lo))) ** gamma
            s += RAMP[1 + int(v * (len(RAMP) - 2) + .5)]
            lifted = [floor + (1 - floor) * (x / 255) ** lift for x in cell[:3]]
            colors.append(_tint(lifted, tint))
            where.append((r, c))
        chars.append(s)

    palette, idx = _quantise(colors, ncolors)
    tones = [[" "] * cols for _ in range(rows)]
    for (r, c), j in zip(where, idx):
        tones[r][c] = "0123456789abcdefghijklmnopqrstuvwxyz"[j]
    return {"cols": cols, "rows": rows, "palette": palette,
            "chars": [s.rstrip() for s in chars], "tones": ["".join(t).rstrip() for t in tones]}


def main():
    from PIL import Image  # only this tool needs Pillow

    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", nargs=4, type=int, help="x0 y0 x1 y1 in the original photo")
    ap.add_argument("--cols", type=int, default=72)
    ap.add_argument("--work-width", type=int, default=421, help="photo is downscaled to this width first")
    args = ap.parse_args()
    img = Image.open(args.photo).convert("RGB")
    scale = args.work_width / img.width
    img = img.resize((args.work_width, round(img.height * scale)), Image.LANCZOS)
    px = img.load()
    rgb = [[px[x, y] for x in range(img.width)] for y in range(img.height)]
    crop = [round(v * scale) for v in args.crop] if args.crop else (0, 0, img.width, img.height)
    save(build(rgb, crop, args.cols))


def save(portrait):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(portrait, f, ensure_ascii=False, indent=0)
    print(f"wrote {OUT}: {portrait['cols']}x{portrait['rows']}, {len(portrait['palette'])} colours")


if __name__ == "__main__":
    main()
