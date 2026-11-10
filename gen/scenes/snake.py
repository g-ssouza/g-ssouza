"""Wraps Platane/snk's animated snake in a panel so it sits on the same dark
background in GitHub's light and dark themes.

The workflow runs snk first and leaves its SVG at dist/snake.svg (or
$SNAKE_SVG). Locally, without that file, the animation nested in the previous
assets/snake.svg is reused; if there is none yet, a static grid from the
calendar stands in."""

import datetime as dt
import os
import re

from ..svg import Doc, label, panel, rect, text

W, H = 1000, 278
DOTS = ["#131B15", "#1F3B28", "#2E6B44", "#62B37F", "#8FD3A6"]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def static_grid(data, x0, y0):
    today = data["today"]
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)  # a Sunday, 53 weeks back
    vals = sorted(v for v in data["cal"].values() if v)
    q = [vals[int(len(vals) * f)] for f in (.25, .5, .75)] if vals else [1, 2, 3]
    out = []
    d = start
    while d <= today:
        week, dow = (d - start).days // 7, (d.weekday() + 1) % 7
        v = data["cal"].get(d, 0)
        lvl = 0 if not v else 1 + sum(v > t for t in q)
        out.append(rect(x0 + week * 16, y0 + dow * 16, 12, 12, DOTS[min(lvl, 4)], extra=' rx="2"'))
        d += dt.timedelta(days=1)
    return "".join(out)


NESTED = re.compile(r'<svg x="[^"]+" y="[^"]+" width="[^"]+" height="[^"]+" viewBox="([^"]+)">(.*?)</svg>', re.S)


def snk_source(src, path):
    """The fresh snk output, or else the animation already nested in our last panel."""
    if os.path.exists(src):
        with open(src, encoding="utf-8") as f:
            return f.read()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            m = NESTED.search(f.read())
        if m:
            print("  reusing the snake from the previous panel")
            return f'<svg viewBox="{m.group(1)}">{m.group(2)}</svg>'
    return None


def render(cfg, data, path):
    src = os.environ.get("SNAKE_SVG", os.path.join(ROOT, "dist", "snake.svg"))
    snk = snk_source(src, path)
    doc = Doc(W, H, "Snake eating the contribution graph",
              "Platane/snk animation: a snake eats its way through the last 12 months of contributions.")
    doc.add(panel(0, 0, W, H, "snake · contributions", "last 12 months"))
    sx, sy = 60, 46
    if snk:
        m = re.match(r"\s*<svg\b([^>]*)>", snk)
        vb = re.search(r'viewBox="([^"]+)"', m.group(1)).group(1)
        _, _, vw, vh = (float(v) for v in vb.split())
        scale = min(880 / vw, 192 / vh)
        inner = snk[m.end():snk.rstrip().rfind("</svg>")]
        doc.add(f'<svg x="{sx + (880 - vw * scale) / 2:g}" y="{sy}" width="{vw * scale:g}" height="{vh * scale:g}" '
                f'viewBox="{vb}">{inner}</svg>')
    else:
        doc.add(static_grid(data, sx + 16, sy + 32),
                text(W / 2, sy + 168, "the snake shows up after the first GitHub Actions run", "dim", 11, anchor="middle"))
    y = H - 20
    doc.add(text(20, y, "each square is a day; the snake eats the ones with contributions", "dim", 11))
    lx = W - 20 - 5 * 16 - 44
    doc.add(label(lx - 8, y, "less", anchor="end"))
    for i, c in enumerate(DOTS):
        doc.add(rect(lx + i * 16, y - 10, 12, 12, c, extra=' rx="2"'))
    doc.add(label(lx + 5 * 16 + 4, y, "more"))
    doc.save(path)
