"""Activity graph: contributions per day over the last 31 days."""

import datetime as dt

from ..svg import GOLD, GOLD2, JADE2, LN, MONTHS, Doc, num, panel, rect, text

W, H = 1000, 300
DAYS = 31


def render(cfg, data, path):
    today = data["today"]
    days = [today - dt.timedelta(days=DAYS - 1 - i) for i in range(DAYS)]
    vals = [data["cal"].get(d, 0) for d in days]
    total = sum(vals)
    doc = Doc(W, H, f"GitHub — activity over the last {DAYS} days",
              f"{total} contributions between {days[0]} and {days[-1]}; at most {max(vals)} in a day.")
    top = max(2, max(vals))
    top += top % 2  # even, so the middle gridline is a whole number

    x0, x1, y0, y1 = 62, W - 26, 62, H - 64
    sx = (x1 - x0) / (DAYS - 1)

    def px(i):
        return x0 + i * sx

    def py(v):
        return y1 - (y1 - y0) * v / top

    doc.define(f'<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD}" stop-opacity=".32"/>'
               f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>')
    pts = [(px(i), py(v)) for i, v in enumerate(vals)]
    line = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    length = sum(((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** .5 for i in range(DAYS - 1))
    doc.style(f".ln{{stroke-dasharray:{length:.0f};animation:draw 2.2s ease-out .2s backwards}}"
              f"@keyframes draw{{from{{stroke-dashoffset:{length:.0f}}}}}"
              ".ar{animation:fade 1s ease-out 1.2s backwards}@keyframes fade{from{opacity:0}}"
              ".pt{animation:fade .3s ease-out backwards}")
    doc.add(panel(0, 0, W, H, f"Activity · last {DAYS} days", f"{num(total)} contributions"))

    # grid + y labels
    for k in range(3):
        v = top * k // 2
        y = py(v)
        dash = "" if k == 0 else ' stroke-dasharray="2 4"'
        doc.add(f'<path d="M{x0} {y + .5:.1f}H{x1}" stroke="{LN}"{dash}/>',
                text(x0 - 12, y + 4, str(v), "dim", 11, anchor="end"))
    # x labels: every day number, month name where it changes
    for i, d in enumerate(days):
        cls = "mut" if d.weekday() == 6 or i == DAYS - 1 else "faint"
        doc.add(text(px(i), y1 + 22, f"{d.day:02d}", cls, 10.5, anchor="middle"))
        if i == 0 or d.day == 1:
            doc.add(text(px(i), y1 + 40, MONTHS[d.month - 1].upper(), "lab gold", anchor="middle"))

    doc.add(f'<path class="ar" d="{line}L{x1} {y1}L{x0} {y1}Z" fill="url(#area)"/>',
            f'<path class="ln" d="{line}" fill="none" stroke="{GOLD2}" stroke-width="2.2" stroke-linejoin="round"/>')
    for i, ((x, y), v) in enumerate(zip(pts, vals)):
        col = JADE2 if v else "rgba(232,228,212,.25)"
        s = 7 if v else 5
        doc.add(f'<g class="pt" style="animation-delay:{0.2 + 2.0 * i / DAYS:.2f}s">'
                f'{rect(x - s / 2, y - s / 2, s, s, col)}</g>')
        if v:
            doc.add(text(x, y - 10, str(v), "jade2", 10.5, anchor="middle"))
    doc.save(path)
