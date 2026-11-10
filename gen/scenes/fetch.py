"""neofetch-style card: coloured ASCII portrait on the left, system info on the
right, live GitHub numbers at the bottom."""

import datetime as dt
import json
import os

from ..svg import GOLD, GOLD2, JADE, JADE2, LN, PN2, RED, SKY, TX, Doc, esc, num, panel, rect, spans, text, tw

W, H = 1000, 644
FS, LH = 13.5, 19.6  # info column
PFS = 8  # portrait font size; cells are PFS*0.6 wide, PFS*1.2 tall


def uptime(born, now):
    """Age as years, months, days; a day only counts once the birth hour has passed."""
    now = now.astimezone(born.tzinfo)
    y, m, d = now.year - born.year, now.month - born.month, now.day - born.day
    if (now.hour, now.minute) < (born.hour, born.minute):
        d -= 1
    if d < 0:
        m -= 1
        d += (now.replace(day=1) - dt.timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    parts = [(y, "year"), (m, "month"), (d, "day")]
    return ", ".join(f"{v} {unit}{'' if v == 1 else 's'}" for v, unit in parts if v)


def portrait(x0, y0):
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "portrait.json"), encoding="utf-8") as f:
        p = json.load(f)
    cw, lh = PFS * 0.6, PFS * 1.2
    rows = []
    for r, (chars, tones) in enumerate(zip(p["chars"], p["tones"])):
        runs, c = [], 0
        while c < len(chars):
            if chars[c] == " ":
                c += 1
                continue
            start = c  # one <text> per contiguous stretch, one <tspan> per colour run
            spans_ = []
            while c < len(chars) and chars[c] != " ":
                t, s = tones[c], c
                while c < len(chars) and chars[c] != " " and tones[c] == t:
                    c += 1
                col = p["palette"]["0123456789abcdefghijklmnopqrstuvwxyz".index(t)]
                spans_.append(f'<tspan fill="{col}">{esc(chars[s:c])}</tspan>')
            runs.append(f'<text x="{x0 + start * cw:.1f}" y="{y0 + (r + 1) * lh:.1f}">{"".join(spans_)}</text>')
        rows.append(f'<g class="pr" style="animation-delay:{r * 16}ms">{"".join(runs)}</g>')
    return "".join(rows), p["cols"] * cw, p["rows"] * lh


def cells(s):
    """Width in monospace cells; CJK glyphs come from a fallback font at ~1em."""
    return sum(1 / 0.6 if ord(ch) >= 0x2E80 else 1 for ch in s)


def row(x, y, key, value, width, kcls="gold", vcls="tx"):
    """'Key: ..... value' with dots up to a right-aligned value."""
    dots = int(width - len(key) - 2 - cells(value) - 1.5)
    right = x + width * FS * 0.6
    return (spans(x, y, [(key, kcls), (": ", "dim"), ("." * max(dots, 1), "faint")], FS)
            + text(right, y, value, vcls, anchor="end"))


def render(cfg, data, path):
    doc = Doc(W, H, f"{cfg['name']} — about me",
              "neofetch-style card: ASCII portrait made from a photo, personal info and GitHub numbers.")
    doc.style(
        f"text{{font-size:{FS}px}}"
        f".pt text{{font-size:{PFS}px}}"
        ".pr{animation:in .25s ease-out backwards}"
        ".ln{animation:in .2s ease-out backwards}"
        "@keyframes in{from{opacity:0}}"
        ".scan{animation:scan 6s linear 2s infinite;transform:translateY(-80px)}"
        "@keyframes scan{0%{transform:translateY(-80px)}55%,100%{transform:translateY(620px)}}"
        ".cur{animation:blink 1s steps(1,end) infinite}@keyframes blink{50%{opacity:0}}"
    )
    doc.add(panel(0, 0, W, H, "okaru@lab: ~ — neofetch", "about me"))

    # portrait
    px, py = 26, 54
    body, pw, ph = portrait(px, py)
    doc.define('<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="{GOLD2}" stop-opacity="0"/><stop offset=".8" stop-color="{GOLD2}" stop-opacity=".10"/>'
               f'<stop offset="1" stop-color="{GOLD2}" stop-opacity=".22"/></linearGradient>'
               f'<clipPath id="pclip"><rect x="{px}" y="{py}" width="{pw:.0f}" height="{ph + 6:.0f}"/></clipPath>')
    doc.add(f'<g class="pt">{body}</g>',
            f'<g clip-path="url(#pclip)"><rect class="scan" x="{px}" y="{py}" width="{pw:.0f}" height="70" fill="url(#scan)"/></g>')

    # info column
    x = px + pw + 34
    width = int((W - 26 - x) / (FS * 0.6))
    y = 74
    lines = []
    host = cfg["host"]
    user, machine = host.split("@")
    lines.append(spans(x, y, [(user, "gold2 b"), ("@", "dim"), (machine, "gold2 b"), (" ", ""),
                              ("─" * (width - len(host) - 1), "faint")], FS))
    born = dt.datetime.fromisoformat(cfg["born"])
    values = {"uptime": uptime(born, dt.datetime.now(dt.timezone.utc)), "email": cfg["links"]["email"]}
    for item in cfg["fetch"]:
        y += LH
        if item is None:
            continue
        if isinstance(item, str):
            if item == "GitHub":
                break
            lines.append(spans(x, y, [("— ", "faint"), (item, "mut"), (" " + "─" * (width - len(item) - 3), "faint")], FS))
            continue
        key, value = item
        lines.append(row(x, y, key, value.format(**values), width))

    # GitHub numbers, two per line like Andrew6rant's card
    lines.append(spans(x, y, [("— ", "faint"), ("GitHub", "mut"), (" " + "─" * (width - 9), "faint")], FS))
    half = (width - 3) // 2
    contrib = f"{num(data['repo_count'])}" + (f" {{Contributed: {data['contributed_to']}}}"
                                              if data.get("contributed_to") is not None else "")
    pairs = [(("Repos", contrib), ("Stars", num(data["stars"]))),
             (("Commits", num(data["commits_total"])), ("Followers", num(data["followers"]))),
             (("Contributions", num(data["contrib_total"])), ("PRs", num(data["prs"])))]
    for (k1, v1), (k2, v2) in pairs:
        y += LH
        d1 = half - len(k1) - 2 - len(v1) - 1
        d2 = (width - half - 3) - len(k2) - 2 - len(v2) - 1
        lines.append(spans(x, y, [(k1, "gold"), (": ", "dim"), ("." * d1 + " ", "faint"), (v1, "jade2"),
                                  (" | ", "dim"), (k2, "gold"), (": ", "dim"), ("." * d2 + " ", "faint"), (v2, "jade2")], FS))

    # neofetch colour blocks + prompt
    y += LH * 1.2
    cols = [PN2, RED, JADE, GOLD, SKY, "#B77BB7", JADE2, TX]
    blocks = "".join(rect(x + i * 26, y, 26, 12, c) for i, c in enumerate(cols))
    y += LH * 1.6
    prompt = spans(x, y, [("okaru@lab", "jade"), (":", "dim"), ("~", "sky"), ("$ ", "dim")], FS)
    cur = rect(x + tw("okaru@lab:~$ ", FS), y - FS * 0.8, FS * 0.6, FS, GOLD, extra=' class="cur"')

    base = 59 * 16 + 150  # after the portrait has drawn in
    for i, ln in enumerate(lines + [blocks, prompt + cur]):
        doc.add(f'<g class="ln" style="animation-delay:{base + i * 45}ms">{ln}</g>')
    doc.add(f'<path d="M{px + pw + 16:.0f} 48V{H - 14}" stroke="{LN}"/>')
    doc.save(path)
