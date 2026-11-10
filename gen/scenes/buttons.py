"""Link buttons under the banner: portfolio, LinkedIn, e-mail.

An SVG inside <img> can't be clicked per region, so each button is its own
image inside its own link. The README puts the three side by side at 33.333%
with no whitespace between them; each image is a third of a 1000-unit row and
the gaps are drawn inside the images, so the row's outer edges line up exactly
with the full-width panels above and below."""

import os

from ..svg import PN, TX, Doc, rect, text

ROW = 1000
GAP = 20            # same 2% gap as between the half-width cards
SLOT = ROW / 3
BTN = (ROW - 2 * GAP) / 3
H = 64
PX = 3              # one sprite pixel
LABEL = 18
SPACING = 2

SPRITES = {
    # the portfolio's entrance TV
    "tv": """
...#...#...
....#.#....
###########
#.......#.#
#.......#.#
#.......###
#.......#.#
###########
.#.......#.
""",
    "in": """
.########.
#........#
#.#......#
#........#
#.#.###..#
#.#.#..#.#
#.#.#..#.#
#.#.#..#.#
#........#
.########.
""",
    "mail": """
###########
##.......##
#.#.....#.#
#..#...#..#
#...#.#...#
#....#....#
#.........#
###########
""",
}
# blinking play button inside the TV screen
PLAY = [(3, 3), (3, 4), (4, 4), (3, 5), (4, 5), (3, 6)]
ICONS = {"portfolio": "tv", "linkedin": "in", "email": "mail"}


def sprite(name):
    rows = SPRITES[name].strip("\n").split("\n")
    return [(c, r) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch == "#"], len(rows[0]), len(rows)


def pix_path(cells, x, y):
    return "".join(f"M{x + c * PX:g} {y + r * PX:g}h{PX}v{PX}h-{PX}z" for c, r in cells)


def notched(x, y, w, h, k=PX):
    """Rectangle with one-pixel notched corners."""
    return (f"M{x + k:g} {y:g}h{w - 2 * k:g}v{k}h{k}v{h - 2 * k:g}h-{k}v{k}"
            f"h-{w - 2 * k:g}v-{k}h-{k}v-{h - 2 * k:g}h{k}z")


def render(cfg, data, path):
    out = os.path.dirname(path)
    for i, b in enumerate(cfg["buttons"]):
        x0 = i * (BTN + GAP) - i * SLOT  # where this button starts inside its own image
        doc = Doc(SLOT, H, b["label"], f"Link: {b['label']} — {b['sub']}", bg=None)
        doc.style(".px{shape-rendering:crispEdges}"
                  ".play{animation:blink 1.06s steps(1,end) infinite}@keyframes blink{50%{opacity:0}}"
                  f".glint{{animation:glint 6s ease-in-out {1.2 + i * .35:.2f}s infinite;transform:translateX(-60px)}}"
                  f"@keyframes glint{{0%{{transform:translateX(-60px)}}30%,100%{{transform:translateX({BTN + 20:g}px)}}}}"
                  f".lbl{{font-size:{LABEL}px;letter-spacing:{SPACING}px}}")
        border = "#363A33"
        doc.define(f'<clipPath id="bar{i}"><rect x="{x0 + PX * 2:g}" y="{H - PX * 3}" width="{BTN - PX * 4:g}" height="{PX}"/></clipPath>')
        doc.add(f'<g class="px"><path d="{notched(x0, 0, BTN, H)}" fill="{border}"/>'
                f'<path d="{notched(x0 + PX, PX, BTN - 2 * PX, H - 2 * PX)}" fill="{PN}"/>'
                f'{rect(x0 + PX * 2, H - PX * 3, BTN - PX * 4, PX, b["color"])}</g>',
                f'<g clip-path="url(#bar{i})"><rect class="glint" x="{x0}" y="{H - PX * 3}" width="48" height="{PX}" '
                f'fill="#fff" fill-opacity=".55"/></g>')

        cells, sw, sh = sprite(ICONS[b["id"]])
        label = b["label"].upper()
        lw = len(label) * (LABEL * 0.6 + SPACING) - SPACING
        gw = sw * PX + 14 + lw
        gx = x0 + (BTN - gw) / 2
        iy = (H - PX * 2 - sh * PX) / 2
        doc.add(f'<g class="px"><path d="{pix_path(cells, gx, iy)}" fill="{b["color"]}"/>')
        if ICONS[b["id"]] == "tv":
            doc.add(f'<path class="play" d="{pix_path(PLAY, gx, iy)}" fill="{TX}"/>')
        doc.add("</g>", text(gx + sw * PX + 14, H / 2 + 3, label, "lbl tx"))
        doc.save(os.path.join(out, f"button-{b['id']}.svg"))
