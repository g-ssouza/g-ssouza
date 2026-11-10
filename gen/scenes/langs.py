"""Top languages as htop-style meters."""

from ..svg import LN2, PN2, Doc, panel, rect, side_pad, text

W, H = 495, 250
TOP = 6
SEGS = 24


def render(cfg, data, path):
    langs = data["languages"][:TOP]
    rest = 1 - sum(l[2] for l in langs)
    doc = Doc(W, H, "GitHub — most used languages", pad=side_pad("right"), desc=
              ", ".join(f"{n} {p * 100:.1f}%" for n, _, p, _, _ in langs))
    doc.style(".ln{font-size:12.5px}.pc{font-size:12px}"
              f".fill{{animation:fill .9s steps({SEGS},end) backwards}}"
              "@keyframes fill{from{clip-path:inset(0 100% 0 0)}}")
    doc.add(panel(0, 0, W, H, "Languages", f"top {TOP}"))

    # one stacked bar for the whole mix
    x0, bw, by = 18, W - 36, 50
    doc.add(rect(x0, by, bw, 8, PN2))
    x = x0
    for name, color, p, _, _ in langs:
        doc.add(rect(x, by, max(bw * p - 1, 1), 8, color))
        x += bw * p
    if rest > 0.001:
        doc.add(rect(x, by, max(x0 + bw - x, 0), 8, "rgba(232,228,212,.18)"))

    # meters: name [|||||||     ] pct
    y0, step = 84, 24
    sw, sg = 9, 3
    mx = 130
    for i, (name, color, p, _, _) in enumerate(langs):
        y = y0 + i * step
        on = round(p * SEGS) if p > 0 else 0
        on = max(on, 1)
        doc.add(text(x0, y, name if len(name) <= 13 else name[:12] + "…", "ln tx"))
        doc.add(text(mx - 8, y, "[", "dim"), text(mx + SEGS * (sw + sg) + 2, y, "]", "dim"))
        segs_off = "".join(rect(mx + k * (sw + sg), y - 11, sw, 13, PN2) for k in range(SEGS))
        segs_on = "".join(rect(mx + k * (sw + sg), y - 11, sw, 13, color) for k in range(on))
        doc.add(segs_off, f'<g class="fill" style="animation-delay:{200 + i * 90}ms">{segs_on}</g>')
        doc.add(text(W - 18, y, f"{p * 100:.1f}%", "pc jade2", anchor="end"))

    doc.add(f'<path d="M1 {H - 30.5}H{W - 1}" stroke="{LN2}" stroke-opacity=".5"/>',
            text(x0, H - 11, "weighted √bytes × √repos · forks and this repo left out", "dim", 10.5))
    doc.save(path)
