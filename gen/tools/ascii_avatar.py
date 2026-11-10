"""ASCII avatar: the photo as coloured characters in JetBrains Mono, the head
rising out of a disc of dim dots, on the profile's dark background.

Not part of the daily render; run it once when the photo changes.

    pip install pillow
    python -m gen.tools.ascii_avatar janela.png --frame window --name avatar-ascii-window

Writes avatar/<name>.svg (1024×1024, font embedded). Social networks want a
PNG: open the SVG in a browser and save a screenshot, or convert it with any
SVG renderer that supports embedded web fonts.
"""

import argparse
import os

from ..svg import Doc, esc
from .avatar import FRAMES, OUT, grow
from .portrait import _background, _tint

# how characters get their colour: "palette" maps tone onto the jade→gold→cream
# ramp (good for backlit photos whose own colours are muddy); "photo" keeps the
# cell's real colour, lifted for the dark background and nudged toward the
# palette, like the README's portrait
COLOURS = {"studio": "photo", "window": "palette"}

SIZE = 1024
FS = 14                         # font size; cells are FS*0.6 wide and FS tall
CW, CH = FS * 0.6, FS
COLS, ROWS = round(SIZE / CW), int(SIZE / CH)
DISC = (512, 560, 432)          # centre x, centre y, radius, canvas pixels (same layout as the pixel avatar)
HEAD_TOP = 64                   # canvas y where the hair starts
RAMP = " .:-~=+*x#%&@"
# tone → colour, dark jade shadows up to cream highlights
STOPS = [(0.0, (0x2A, 0x5C, 0x3C)), (0.3, (0x4F, 0x9A, 0x69)), (0.55, (0x8F, 0xD3, 0xA6)),
         (0.75, (0xD8, 0xB2, 0x4A)), (1.0, (0xF6, 0xEE, 0xD8))]
BG = "#0A0F0B"
DOT = "#24402D"                 # the disc's dots
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def colour(t):
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return "#%02x%02x%02x" % tuple(round(ca[i] + (cb[i] - ca[i]) * f) for i in range(3))
    return "#%02x%02x%02x" % STOPS[-1][1]


def cells(rgb, fr):
    """Average the photo into the character grid (tone per cell, None for background)."""
    h, w = len(rgb), len(rgb[0])
    lum = [[(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b in row] for row in rgb]
    sat = [[(max(p) - min(p)) / 255 for p in row] for row in rgb]
    bg = grow(_background(lum, sat, w, h, fr["bg_lum"], fr["bg_sat"]), 2)
    k = fr["scale"] / (SIZE / 128)          # photo pixels per canvas pixel, same framing as the pixel avatar
    x0 = fr["center"] - SIZE / 2 * k
    y0 = fr["top"] - HEAD_TOP * k
    wr, wg, wb = fr["weights"]
    grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            xa, xb = x0 + c * CW * k, x0 + (c + 1) * CW * k
            ya, yb = y0 + r * CH * k, y0 + (r + 1) * CH * k
            tot = n = total = 0
            acc = [0, 0, 0]
            for y in range(int(ya), max(int(yb), int(ya) + 1)):
                for x in range(int(xa), max(int(xb), int(xa) + 1)):
                    total += 1
                    if 0 <= x < w and 0 <= y < h and not bg[y][x]:
                        pr, pg, pb = rgb[y][x]
                        tot += (wr * pr + wg * pg + wb * pb) / 255
                        acc[0] += pr; acc[1] += pg; acc[2] += pb
                        n += 1
            row.append((tot / n, [v / n for v in acc]) if n * 2 > total else None)
        grid.append(row)
    return grid


def build(rgb, fr, mode="palette", k=1.1, reach=2, gamma=0.95):
    # photo mode follows the README portrait's recipe: plain ramp, no dithering
    ramp, dither = (" .:-=+*#%@", False) if mode == "photo" else (RAMP, True)
    if mode == "photo":
        k, gamma = 1.4, .8
    cellgrid = cells(rgb, fr)
    grid = [[cell[0] if cell else None for cell in row] for row in cellgrid]
    tone = [[None] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            v = grid[r][c]
            if v is None:
                continue
            near = [grid[rr][cc] for rr in range(r - reach, r + reach + 1) for cc in range(c - 2 * reach, c + 2 * reach + 1)
                    if 0 <= rr < ROWS and 0 <= cc < COLS and grid[rr][cc] is not None]
            tone[r][c] = v + k * (v - sum(near) / len(near))
    vals = sorted(v for row in tone for v in row if v is not None)
    lo, hi = vals[int(len(vals) * .03)], vals[int(len(vals) * .99)]
    body_row = fr["body_row"] / 128 * SIZE / CH

    dx, dy, dr = DISC
    out = []  # (row, col, char, colour)
    for r in range(ROWS):
        for c in range(COLS):
            cx, cy = (c + .5) * CW, (r + .5) * CH
            d = ((cx - dx) ** 2 + (cy - dy) ** 2) ** .5
            inside = d <= dr
            v = tone[r][c]
            if v is not None and (inside or cy < dy):
                t = min(1, max(0, (v - lo) / (hi - lo))) ** gamma
                body = min(1.0, max(0.0, (r - body_row) / (ROWS - body_row)))
                t = max(0.0, t - .45 * body * body * (3 - 2 * body))
                # ordered dither between neighbouring characters gives flat areas a texture
                x = 2 + t * (len(ramp) - 3)
                if dither:
                    i = min(int(x + (x - int(x) > (BAYER[r % 4][c % 4] + .5) / 16)), len(ramp) - 1)
                else:
                    i = min(int(x + .5), len(ramp) - 1)
                if mode == "photo":
                    # hue from the photo (nudged toward the palette), brightness from the tone,
                    # so eyes, glasses and beard stay dark against the skin
                    tinted = _tint([(x / 255) ** .8 for x in cellgrid[r][c][1]], .35)
                    lum = max(.02, .2126 * tinted[0] + .7152 * tinted[1] + .0722 * tinted[2])
                    target = .16 + .84 * t
                    col = "#%02x%02x%02x" % tuple(round(min(1, v * target / lum) * 255) for v in tinted)
                else:
                    col = colour(t)
                out.append((r, c, ramp[i], col))
            elif inside:
                # the disc: a dotted field, sparser toward the rim
                fade = max(0.0, (d - dr * .7) / (dr * .3))
                if (BAYER[r % 4][c % 4] + .5) / 16 > fade * .8:
                    out.append((r, c, ":" if (r + c) % 2 else ".", DOT))
    return out


def render(chars, title):
    doc = Doc(SIZE, SIZE, title, "ASCII portrait made from a photo.", bg=BG)
    doc.style(f"text{{font-size:{FS}px}}")
    grid = {}
    for r, c, ch, col in chars:
        grid[r, c] = (ch, col)
    for r in range(ROWS):
        y = (r + 1) * CH - FS * 0.22
        c = 0
        while c < COLS:
            if (r, c) not in grid:
                c += 1
                continue
            start, spans = c, []  # one <text> per contiguous run, one <tspan> per colour
            while (r, c) in grid:
                col, run = grid[r, c][1], ""
                while (r, c) in grid and grid[r, c][1] == col:
                    run += grid[r, c][0]
                    c += 1
                spans.append(f'<tspan fill="{col}">{esc(run)}</tspan>')
            doc.add(f'<text x="{start * CW:.2f}" y="{y:.2f}">{"".join(spans)}</text>')
    return doc


def save(rgb, frame, name):
    os.makedirs(OUT, exist_ok=True)
    doc = render(build(rgb, FRAMES[frame], COLOURS.get(frame, "palette")), "Hikaru Ogasawara — ASCII avatar")
    doc.save(os.path.join(OUT, f"{name}.svg"))


def main():
    from PIL import Image  # only the tools need Pillow

    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--frame", choices=sorted(FRAMES), default="window")
    ap.add_argument("--name", default="avatar-ascii")
    args = ap.parse_args()
    img = Image.open(args.photo).convert("RGB")
    width = FRAMES[args.frame]["width"]
    if width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    p = img.load()
    save([[p[x, y] for x in range(img.width)] for y in range(img.height)], args.frame, args.name)


if __name__ == "__main__":
    main()
