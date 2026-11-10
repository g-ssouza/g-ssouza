"""Tiny SVG toolkit shared by every scene: palette, text, panels, icons.

Everything is plain SVG + CSS keyframes. GitHub renders README images through
<img>, which runs CSS animation but never JavaScript, so that is all we use.
"""

import html
import json
import os
import re

from . import fonts

# the portfolio's palette (Portifolio/src/styles.css, .okr)
BG = "#0A0F0B"
PN = "#0D130F"
PN2 = "#131B15"
LN = "rgba(232,228,212,.11)"
LN2 = "rgba(232,228,212,.2)"
TX = "#E8E4D4"
MUT = "#A3AD9F"
DIM = "#7F8A7C"
FAINT = "#4A564C"
GOLD = "#D8B24A"
GOLD2 = "#F0CE6A"
JADE = "#62B37F"
JADE2 = "#8FD3A6"
SKY = "#7FB2DA"
RED = "#E07A6E"

CW = 0.6  # JetBrains Mono advance width, in em

BASE_CSS = (
    "text{font-family:'JBM','JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace;"
    f"fill:{TX};white-space:pre}}"
    ".jp{font-family:'DG','DotGothic16','Hiragino Sans','Yu Gothic','Noto Sans CJK JP',sans-serif}"
    f".tx{{fill:{TX}}}.mut{{fill:{MUT}}}.dim{{fill:{DIM}}}.faint{{fill:{FAINT}}}.gold{{fill:{GOLD}}}"
    f".gold2{{fill:{GOLD2}}}.jade{{fill:{JADE}}}.jade2{{fill:{JADE2}}}.sky{{fill:{SKY}}}.red{{fill:{RED}}}"
    ".b{font-weight:700}.lab{font-size:10.5px;letter-spacing:1.9px}"
)

_ICONS = None

# extra line glyphs for the stats panels, same 24-unit grid as the portfolio's
GLYPHS = {
    "commit": "M2 12h6M16 12h6M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z",
    "pr": "M6 3a2 2 0 1 0 0 4a2 2 0 1 0 0-4zM6 17a2 2 0 1 0 0 4a2 2 0 1 0 0-4zM18 17a2 2 0 1 0 0 4a2 2 0 1 0 0-4zM6 7v10M18 17V9a3 3 0 0 0-3-3h-4M13 3.5L10.5 6L13 8.5",
    "issue": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18zM12 11a1 1 0 1 0 0 2a1 1 0 1 0 0-2z",
    "star": "M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z",
    "people": "M9 5a3 3 0 1 0 0 6a3 3 0 1 0 0-6zM3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5a3 3 0 0 1 0 6M18 14c2 .6 3 2.6 3 6",
    "calendar": "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4",
    "pulse": "M2 12h4l3-7 4 14 3-7h6",
    "repo": "M5 4h11l3 3v13H5zM9 4v6l2-1.5L13 10V4M8 15h8",
}


def esc(s):
    return html.escape(str(s), quote=True)


MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# README layout: half-width cards sit side by side at exactly 50% each, so the
# gap between them is drawn inside the SVGs as transparent padding (GitHub
# strips CSS, and whitespace between images would break the alignment)
GAP = 10


def side_pad(side):
    return {"left": (0, GAP), "right": (GAP, 0)}.get(side, (0, 0))


def num(n):
    """Thousands separator; None shows as a dash."""
    return "—" if n is None else f"{n:,}"


def date_en(d, year=True):
    return f"{MONTHS[d.month - 1]} {d.day}" + (f", {d.year}" if year else "")


def tw(text, size, spacing=0.0):
    """Rendered width of monospace text."""
    return len(text) * (size * CW + spacing)


def text(x, y, s, cls="", size=None, anchor=None, extra=""):
    attrs = f' class="{cls}"' if cls else ""
    if size:
        attrs += f' font-size="{size}"'
    if anchor:
        attrs += f' text-anchor="{anchor}"'
    return f'<text x="{x:g}" y="{y:g}"{attrs}{extra}>{esc(s)}</text>'


def spans(x, y, parts, size=None, extra=""):
    """One <text> made of differently styled runs: parts = [(text, cls), ...]."""
    inner = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' if c else esc(t) for t, c in parts)
    fs = f' font-size="{size}"' if size else ""
    return f'<text x="{x:g}" y="{y:g}"{fs}{extra}>{inner}</text>'


def label(x, y, s, cls="dim", anchor=None):
    """Uppercase tracked panel label, like the portfolio's .lab-t."""
    return text(x, y, s.upper(), f"lab {cls}", anchor=anchor)


def rect(x, y, w, h, fill="none", stroke=None, extra=""):
    st = f' stroke="{stroke}"' if stroke else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{st}{extra}/>'


def panel(x, y, w, h, left=None, right=None, head=34, fill=PN):
    """Bordered panel with an optional header row (left label, gold right label)."""
    out = [rect(x + .5, y + .5, w - 1, h - 1, fill, LN2)]
    if left or right:
        out.append(f'<path d="M{x + 1} {y + head + .5}H{x + w - 1}" stroke="{LN}"/>')
        if left:
            out.append(label(x + 14, y + head / 2 + 4, left))
        if right:
            out.append(label(x + w - 14, y + head / 2 + 4, right, "gold", anchor="end"))
    return "".join(out)


def icons():
    global _ICONS
    if _ICONS is None:
        with open(os.path.join(os.path.dirname(__file__), "data", "icons.json"), encoding="utf-8") as f:
            _ICONS = json.load(f)
    return _ICONS


def icon(name, x, y, size, color, sw=1.7):
    """Simple Icons logo (filled) or portfolio line glyph (stroked), 24-unit grid."""
    ic = icons()
    k = size / 24
    if name in ic["logos"]:
        body = f'<path d="{ic["logos"][name]}" fill="{color}"/>'
    else:
        d = GLYPHS.get(name) or ic["glyphs"][name]
        body = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<g transform="translate({x:g} {y:g}) scale({k:g})">{body}</g>'


def wrap(s, width):
    """Greedy word wrap to `width` characters."""
    lines, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    if cur:
        lines.append(cur)
    return lines


_TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")


class Doc:
    def __init__(self, w, h, title, desc="", pad=(0, 0), bg=BG):
        """w×h is the drawing; pad=(left, right) adds transparent margin beside it."""
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.pad, self.bg = pad, bg
        self.css, self.defs, self.body = [], [], []

    def add(self, *parts):
        self.body.extend(parts)
        return self

    def style(self, css):
        self.css.append(css)
        return self

    def define(self, d):
        self.defs.append(d)
        return self

    def _font_css(self, body):
        jbm, dg = set(), set()
        for attrs, inner in _TEXT_RE.findall(body):
            chars = html.unescape(_TAG_RE.sub("", inner))
            (dg if "jp" in attrs else jbm).update(chars)
        return fonts.face("JBM", jbm) + fonts.face("DG", dg)

    def render(self):
        body = "".join(self.body)
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        css = self._font_css(body) + BASE_CSS + "".join(self.css)
        desc = f"<desc>{esc(self.desc)}</desc>" if self.desc else ""
        left, right = self.pad
        w = self.w + left + right
        bg = rect(0, 0, self.w, self.h, self.bg) if self.bg else ""
        content = f'<g transform="translate({left:g} 0)">{bg}{body}</g>' if left else bg + body
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{self.h}" '
            f'viewBox="0 0 {w:g} {self.h}" role="img" aria-labelledby="title">'
            f'<title id="title">{esc(self.title)}</title>{desc}{defs}<style>{css}</style>'
            f'{content}</svg>\n'
        )

    def save(self, path):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.render())
        print(f"  wrote {os.path.relpath(path)} ({os.path.getsize(path) / 1024:.1f} KB)")
