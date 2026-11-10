"""Trophy shelf: eight pixel trophies ranked C → SSS from live numbers, with
progress to the next rank. Locked ones stay grey."""

from ..svg import DIM, FAINT, LN, PN2, Doc, num, panel, rect, side_pad, text

W, H = 495, 250
RANKS = ["C", "B", "A", "AA", "AAA", "S", "SS", "SSS"]
TIER = {"C": "#B07B4A", "B": "#A3AD9F", "A": "#D8B24A", "AA": "#E3BE55", "AAA": "#F0CE6A",
        "S": "#8FD3A6", "SS": "#7FD3C8", "SSS": "#E8E4D4"}

CUP = [  # 12×12
    "..########..",
    "##.######.##",
    "#..######..#",
    "#..######..#",
    ".#.######.#.",
    "...######...",
    "....####....",
    ".....##.....",
    ".....##.....",
    "....####....",
    "...######...",
    "...######...",
]


def cup(x, y, s, color, shade):
    out = []
    for r, line in enumerate(CUP):
        for c, ch in enumerate(line):
            if ch == "#":
                col = shade if c >= 7 and r < 7 else color
                out.append(rect(x + c * s, y + r * s, s, s, col))
    out.append(rect(x + 3 * s, y + s, s, 3 * s, "rgba(255,255,255,.35)"))  # glint
    return "".join(out)


def rank_of(value, steps):
    got = None
    for name, need in zip(RANKS, steps):
        if value >= need:
            got = name
    nxt = next(((n, need) for n, need in zip(RANKS, steps) if value < need), None)
    return got, nxt


def render(cfg, data, path):
    years = (data["today"] - data["created"]).days / 365.25
    items = [  # title, value, thresholds C..SSS, unit shown after the numbers
        ("Commits", data["commits_total"], [1, 10, 100, 200, 500, 1000, 2000, 4000], ""),
        ("Repositories", data["repo_count"], [1, 5, 10, 20, 30, 40, 45, 50], ""),
        ("Pull requests", data["prs"], [1, 10, 20, 50, 100, 200, 500, 1000], ""),
        ("Contributions", data["contrib_total"], [1, 50, 100, 250, 500, 1000, 2500, 5000], ""),
        ("Polyglot", len(data["languages"]), [1, 2, 4, 6, 8, 10, 12, 15], " langs"),
        ("Veteran", int(years), [1, 2, 3, 4, 5, 7, 10, 15], " yrs"),
        ("Stars", data["stars"], [1, 10, 30, 50, 100, 200, 700, 2000], ""),
        ("Followers", data["followers"], [1, 10, 20, 50, 100, 200, 400, 1000], ""),
    ]
    got = [rank_of(v, steps) for _, v, steps, _ in items]
    unlocked = sum(1 for g, _ in got if g)
    doc = Doc(W, H, "GitHub — trophies",
              "; ".join(f"{t}: {g or 'locked'}" for (t, *_), (g, _) in zip(items, got)), pad=side_pad("right"))
    doc.style(".tt{font-size:9.5px;letter-spacing:1px}.tv{font-size:10.5px}.rk{font-size:13px}"
              ".cupin{animation:pop .5s cubic-bezier(.2,.9,.3,1.4) backwards}"
              "@keyframes pop{from{opacity:0;transform:translateY(6px)}}")
    doc.add(panel(0, 0, W, H, "Achievements", f"{unlocked}/{len(items)} unlocked"))

    cw, ch = (W - 24) / 4, 98
    for i, ((title, value, steps, unit), (rank, nxt)) in enumerate(zip(items, got)):
        x = 12 + (i % 4) * cw
        y = 44 + (i // 4) * (ch + 4)
        cx = x + cw / 2
        color = TIER[rank] if rank else "#26302A"
        shade = "#00000055" if rank else "#1E2621"
        doc.add(rect(x + 3.5, y + .5, cw - 7, ch - 1, PN2, LN),
                f'<g class="cupin" style="animation-delay:{i * 70}ms">{cup(cx - 28, y + 10, 3, color, shade)}</g>',
                f'<text x="{cx + 14:.1f}" y="{y + 44}" class="rk b" fill="{color if rank else FAINT}">{rank or "?"}</text>',
                text(cx, y + 64, title.upper(), "tt mut" if rank else "tt faint", anchor="middle"))
        if nxt:
            k = RANKS.index(nxt[0])
            prev = steps[k - 1] if k else 0
            frac = max(0.0, min(1.0, (value - prev) / (nxt[1] - prev)))
            sub = f"{num(value)} / {num(nxt[1])}{unit}"
        else:
            frac, sub = 1.0, f"{num(value)}{unit} · max"
        bx, bw = x + 14, cw - 28
        doc.add(text(cx, y + 79, sub, "tv dim" if rank else "tv faint", anchor="middle"),
                rect(bx, y + 86, bw, 3, "rgba(232,228,212,.08)"),
                rect(bx, y + 86, max(bw * frac, 0), 3, color if rank else DIM))
    doc.save(path)
