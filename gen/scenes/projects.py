"""One card per project (each linked from the README to its repository) plus a
wide card for the portfolio itself. Repo facts (language, stars, last push)
are read live; the text comes from the portfolio's project list."""

import datetime as dt
import os

from ..github import LINGUIST_COLORS
from ..svg import (BG, DIM, FAINT, GOLD, GOLD2, LN, LN2, PN2, Doc, date_en, icon, panel, rect, side_pad, spans,
                   text, tw, wrap)

W, H = 495, 258
def when(iso):
    return date_en(dt.date.fromisoformat(iso))


def repo_info(data, full):
    if not full:
        return None
    for r in data["repos"]:
        if r["full"] == full:
            return r
    return data["extra"].get(full)


def chips(x, y, items, size=10.5, max_x=None):
    out, cx = [], x
    for it in items:
        w = tw(it, size) + 16
        if max_x and cx + w > max_x:
            break
        out.append(rect(cx + .5, y + .5, w - 1, 22, "rgba(232,228,212,.03)", LN2))
        out.append(text(cx + 8, y + 15.5, it, "chip", size))
        cx += w + 6
    return "".join(out)


def footer(y, info, link_text):
    out = [f'<path d="M1 {y + .5}H{W - 1}" stroke="{LN}"/>']
    fy = y + 22
    if info:
        x = 16
        if info.get("lang"):
            out.append(rect(x, fy - 9, 9, 9, info.get("lang_color") or LINGUIST_COLORS.get(info["lang"], DIM)))
            out.append(text(x + 15, fy, info["lang"], "ft mut"))
            x += 15 + tw(info["lang"], 12) + 18
        out.append(spans(x, fy, [("★ ", "gold"), (str(info["stars"]), "mut")], 12))
        x += tw(f"★ {info['stars']}", 12) + 18
        out.append(spans(x, fy, [("updated ", "dim"), (when(info["pushed"]), "mut")], 12))
    else:
        out.append(text(16, fy, "no public repository", "ft dim"))
    out.append(text(W - 16, fy, link_text, "ft gold2", anchor="end"))
    return "".join(out)


def card(p, info, path, side):
    doc = Doc(W, H, f"{p['title']} — {p['tags']}", p["line"], pad=side_pad(side))
    doc.style(".chip{fill:#C9CBBE}.ft{font-size:12px}.ds{font-size:13.5px}"
              ".gl{animation:gl 5s ease-in-out infinite}@keyframes gl{0%,100%{opacity:.35}50%{opacity:.9}}")
    doc.add(panel(0, 0, W, H, f"{p['num']} · {p['tags']}", p["period"]))
    # icon tile
    doc.add(rect(16.5, 50.5, 43, 43, PN2, "rgba(216,178,74,.42)"),
            icon(p["icon"], 25, 59, 26, p["color"]))
    doc.add(text(74, 70, p["title"], "tx b", 22))
    doc.add(text(74, 90, info["full"] if info else "academic project", "dim", 11.5))
    desc = p["line"] + (f" ({p['credit']}.)" if p.get("credit") else "")
    lines = wrap(desc, int((W - 32) / (13.5 * .6)))[:4]
    for k, ln in enumerate(lines):
        doc.add(text(16, 124 + k * 20, ln, "ds mut"))
    doc.add(chips(16, 124 + 4 * 20 - 6, p["stack"], 11, max_x=W - 16))
    doc.add(footer(H - 36, info, "open repository →" if info else "see portfolio →"))
    doc.save(path)


def tv(x, y, s=4):
    """Pixel-art CRT, drawn on a 24×20 grid."""
    px = []
    def box(c, r, w, h, col):
        px.append(rect(x + c * s, y + r * s, w * s, h * s, col))
    box(8, 0, 1, 3, FAINT); box(15, 0, 1, 3, FAINT); box(9, 2, 1, 1, FAINT); box(14, 2, 1, 1, FAINT)
    box(10, 3, 4, 1, FAINT)
    box(0, 4, 24, 15, "#2A3A2E")
    box(1, 5, 22, 13, "#1A241D")
    box(2, 6, 16, 11, BG)
    box(19, 7, 3, 3, GOLD); box(19, 11, 3, 1, FAINT); box(19, 13, 3, 1, FAINT); box(19, 15, 3, 1, FAINT)
    box(3, 19, 3, 1, FAINT); box(18, 19, 3, 1, FAINT)
    scr = "".join(rect(x + 2 * s, y + (6 + k) * s + s - 1, 16 * s, 1, "rgba(143,211,166,.10)") for k in range(11))
    play = (f'<path class="blink" d="M{x + 8 * s} {y + 9 * s}l{4 * s} {2.5 * s}l-{4 * s} {2.5 * s}z" fill="{GOLD2}"/>')
    return "".join(px) + scr + play


def wide(c, path):
    w, h = 1000, 196
    doc = Doc(w, h, f"{c['title']} — the site is a game", c["line"])
    doc.style(".chip{fill:#C9CBBE}.ft{font-size:11.5px}.ds{font-size:13px}"
              ".blink{animation:blink 1.4s steps(1,end) infinite}@keyframes blink{70%{opacity:0}}")
    doc.add(panel(0, 0, w, h, "05 · web · pixel art", "live"))
    doc.add(tv(28, 52, 5))
    x = 178
    doc.add(text(x, 76, c["title"], "tx b", 24),
            text(x + tw(c["title"], 24) + 14, 75, "hikaru-0gasawara.github.io/Portifolio", "gold", 13))
    for k, ln in enumerate(wrap(c["line"], int((w - x - 230) / (13 * .6)))[:3]):
        doc.add(text(x, 104 + k * 19, ln, "ds mut"))
    doc.add(chips(x, 152, c["stack"]))
    doc.add(f'<path d="M{w - 210.5} 48V{h - 14}" stroke="{LN}"/>',
            text(w - 105, 98, "PRESS START", "jp gold2 blink", 22, anchor="middle"),
            text(w - 105, 128, c["langs"], "jp mut", 14, anchor="middle"),
            text(w - 105, 160, "open portfolio →", "ft gold", anchor="middle"))
    doc.save(path)


def render(cfg, data, path):
    out = os.path.dirname(path)
    for i, p in enumerate(cfg["projects"]):
        card(p, repo_info(data, p.get("repo")), os.path.join(out, f"project-{p['id']}.svg"), ("left", "right")[i % 2])
    c = cfg["portfolio_card"]
    wide(c, os.path.join(out, "project-portfolio.svg"))
