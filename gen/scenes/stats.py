"""GitHub stats card: the usual numbers, plus a level ring where XP is simply
the all-time contribution count."""

import math

from ..svg import GOLD, GOLD2, LN, PN2, Doc, icon, label, num, panel, side_pad, text

W, H = 495, 250


def level(xp):
    """LV n starts at 10·(n-1)² XP: quick early levels, slower later."""
    lv = int(math.sqrt(xp / 10)) + 1
    lo, hi = 10 * (lv - 1) ** 2, 10 * lv ** 2
    return lv, lo, hi


def render(cfg, data, path):
    rows = [
        ("pulse", "Contributions (total)", data["contrib_total"]),
        ("calendar", "Last 12 months", data["contrib_year"]),
        ("commit", "Commits", data["commits_total"]),
        ("pr", "Pull requests", data["prs"]),
        ("issue", "Issues", data["issues"]),
        ("star", "Stars earned", data["stars"]),
        ("people", "Followers", data["followers"]),
    ]
    doc = Doc(W, H, "GitHub — stats", "; ".join(f"{k}: {num(v)}" for _, k, v in rows), pad=side_pad("left"))
    doc.style(".rl{font-size:12.5px}.rv{font-size:13px}"
              ".ring{animation:ring 1.4s cubic-bezier(.2,.8,.2,1) .3s backwards}"
              ".row{animation:in .3s ease-out backwards}@keyframes in{from{opacity:0;transform:translateX(-6px)}}")
    doc.add(panel(0, 0, W, H, "GitHub · status", "@" + cfg["login"].lower()))

    y0, step = 64, 25
    for i, (ic, k, v) in enumerate(rows):
        y = y0 + i * step
        doc.add(f'<g class="row" style="animation-delay:{i * 60}ms">'
                f'{icon(ic, 18, y - 12, 15, GOLD, sw=1.9)}'
                f'{text(44, y, k, "rl tx")}{text(300, y, num(v), "rv jade2 b", anchor="end")}</g>')
        if i < len(rows) - 1:
            doc.add(f'<path d="M44 {y + 8.5}H300" stroke="{LN}"/>')

    # level ring
    xp = data["contrib_total"]
    lv, lo, hi = level(xp)
    frac = (xp - lo) / (hi - lo) if hi > lo else 0
    cx, cy, r = 400, 134, 54
    circ = 2 * math.pi * r
    doc.style(f"@keyframes ring{{from{{stroke-dashoffset:{circ:.1f}}}}}")
    doc.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PN2}" stroke="rgba(232,228,212,.08)" stroke-width="8"/>',
            f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD2}" stroke-width="8" '
            f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - frac):.1f}" '
            f'transform="rotate(-90 {cx} {cy})"/>',
            label(cx, cy - 18, "level", anchor="middle"),
            text(cx, cy + 16, f"LV {lv}", "gold2 b", 28, anchor="middle"),
            text(cx, cy + r + 32, f"{num(xp)} / {num(hi)} XP", "mut", 12, anchor="middle"),
            text(cx, cy + r + 48, "XP = contributions", "dim", 10.5, anchor="middle"))
    doc.save(path)
