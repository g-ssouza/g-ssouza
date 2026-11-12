"""Header: pixel-block name that decodes column by column, the hardware→security
path with a packet running through it, and a prompt that types lines from the
portfolio."""

from ..svg import BG, DIM, FAINT, GOLD, GOLD2, LN, LN2, Doc, esc, label, rect, spans, text, tw

W, H = 1200, 400
X0 = 78

# 5×7 bitmap glyphs, just the letters the name needs
GLYPHS = {
    "H": ["1...1", "1...1", "1...1", "11111", "1...1", "1...1", "1...1"],
    "I": ["11111", "..1..", "..1..", "..1..", "..1..", "..1..", "11111"],
    "K": ["1...1", "1..1.", "1.1..", "11...", "1.1..", "1..1.", "1...1"],
    "A": [".111.", "1...1", "1...1", "11111", "1...1", "1...1", "1...1"],
    "R": ["1111.", "1...1", "1...1", "1111.", "1.1..", "1..1.", "1...1"],
    "U": ["1...1", "1...1", "1...1", "1...1", "1...1", "1...1", ".111."],
    "O": [".111.", "1...1", "1...1", "1...1", "1...1", "1...1", ".111."],
    "G": [".111.", "1...1", "1....", "1.111", "1...1", "1...1", ".1111"],
    "S": [".1111", "1....", "1....", ".111.", "....1", "....1", "1111."],
    "W": ["1...1", "1...1", "1...1", "1.1.1", "1.1.1", "1.1.1", ".1.1."],
    " ": ["....."] * 7,

    'T': ['11111', '..1..', '..1..', '..1..', '..1..', '..1..', '..1..'],
    'V': ['1...1', '1...1', '1...1', '1...1', '1...1', '.1.1.', '..1..'],
    'Z': ['11111', '....1', '...1.', '..1..', '.1...', '1....', '11111'],
    'E': ['11111', '1....', '1....', '1111.', '1....', '1....', '11111'],
    'M': ['1...1', '11.11', '1.1.1', '1...1', '1...1', '1...1', '1...1'],
    'N': ['1...1', '11..1', '1.1.1', '1..11', '1...1', '1...1', '1...1'],
    'Y': ['1...1', '1...1', '.1.1.', '..1..', '..1..', '..1..', '..1..'],
    'B': ['1111.', '1...1', '1...1', '1111.', '1...1', '1...1', '1111.'],
    'C': ['.111.', '1...1', '1....', '1....', '1....', '1...1', '.111.'],
    'D': ['1111.', '1...1', '1...1', '1...1', '1...1', '1...1', '1111.'],
    'F': ['11111', '1....', '1....', '1111.', '1....', '1....', '1....'],
    'J': ['..111', '...1.', '...1.', '...1.', '...1.', '1..1.', '.11..'],
    'L': ['1....', '1....', '1....', '1....', '1....', '1....', '11111'],
    'P': ['1111.', '1...1', '1...1', '1111.', '1....', '1....', '1....'],
    'Q': ['.111.', '1...1', '1...1', '1...1', '1.1.1', '1..1.', '.11.1'],
    'X': ['1...1', '1...1', '.1.1.', '..1..', '.1.1.', '1...1', '1...1'],
}


def pixels(word):
    """(col, row) of every lit pixel, 6 columns per letter."""
    out = []
    for i, ch in enumerate(word):
        for r, row in enumerate(GLYPHS[ch]):
            out += [(i * 6 + c, r) for c, on in enumerate(row) if on == "1"]
    return out, len(word) * 6 - 1


def block_path(px, x0, y0, p, dx=0, dy=0):
    s = p - 1
    return "".join(f"M{x0 + c * p + dx} {y0 + r * p + dy}h{s}v{s}h-{s}z" for c, r in px)


def typing(phrases, x, y, size, prompt_w, type_ms=55, hold_ms=2300, erase_ms=20, gap_ms=420):
    """A single clip window + cursor walk through every phrase in one keyframe track."""
    cw = size * 0.6
    segs, t = [], 0
    for p in phrases:
        n = len(p)
        a, b = t, t + n * type_ms
        c, d = b + hold_ms, b + hold_ms + n * erase_ms
        segs.append((a, b, c, d, n))
        t = d + gap_ms
    total = t

    def pct(ms):
        return f"{ms / total * 100:.3f}%"

    frames = []
    for a, b, c, d, n in segs:
        dx = n * cw
        frames += [f"{pct(a)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}",
                   f"{pct(b)}{{transform:translateX({dx:g}px);animation-timing-function:steps(1,end)}}",
                   f"{pct(c)}{{transform:translateX({dx:g}px);animation-timing-function:steps({n},end)}}",
                   f"{pct(d)}{{transform:translateX(0);animation-timing-function:steps(1,end)}}"]
    css = [f"@keyframes ty{{{''.join(frames)}100%{{transform:translateX(0)}}}}",
           f".ty{{transform:translateX({segs[0][4] * cw:g}px);animation:ty {total}ms linear infinite}}",
           f".cur{{animation:blink 1s steps(1,end) infinite}}@keyframes blink{{50%{{opacity:0}}}}"]
    body = []
    maxw = max(len(p) for p in phrases) * cw + 40
    tx = x + prompt_w
    for i, (p, (a, b, c, d, n)) in enumerate(zip(phrases, segs)):
        start = "0%{opacity:1}" if a == 0 else f"0%{{opacity:0}}{pct(a)}{{opacity:1}}"
        css.append(f"@keyframes tv{i}{{{start}{pct(d)}{{opacity:0}}100%{{opacity:0}}}}"
                   f".tv{i}{{opacity:{1 if i == 0 else 0};animation:tv{i} {total}ms steps(1,end) infinite}}")
        body.append(f'<g class="tv{i}">{text(tx, y, p, "tx", size)}</g>')
    clip = f'<clipPath id="tyc"><rect class="ty" x="{tx - maxw:g}" y="{y - size * 1.2:g}" width="{maxw:g}" height="{size * 1.8:g}"/></clipPath>'
    cursor = (f'<g class="ty"><rect class="cur" x="{tx + 1:g}" y="{y - size * 0.82:g}" width="{cw - 1:g}" '
              f'height="{size * 1.02:g}" fill="{GOLD}"/></g>')
    return clip, "".join(css), f'<g clip-path="url(#tyc)">{"".join(body)}</g>{cursor}'


def render(cfg, data, path):
    doc = Doc(W, H, f"{cfg['name']} — {cfg['role']}",
              "Animated banner: pixel-block name, the path from pin to SIEM and a typing prompt.")

    # backdrop: faint dot grid + CRT scanlines, like the portfolio's TV
    doc.define(
        '<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
        '<rect x="7.5" y="7.5" width="1" height="1" fill="rgba(232,228,212,.07)"/></pattern>'
        '<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="rgba(0,0,0,.18)"/></pattern>'
        f'<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{GOLD2}"/>'
        f'<stop offset="1" stop-color="{GOLD}"/></linearGradient>'
        '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )
    doc.add(rect(0, 0, W, H, "url(#dots)"))

    # window chrome
    doc.add(f'<path d="M0 40.5H{W}" stroke="{LN}"/>',
            label(W - 20, 25, cfg["location"], "gold", anchor="end"))
    for i, col in enumerate((GOLD, FAINT, FAINT)):
        doc.add(rect(20 + i * 15, 15, 9, 9, col))

    doc.add(f'<rect x="{X0}" y="70" width="4" height="13" fill="{GOLD}"/>',
            label(X0 + 14, 81, cfg["banner"]["kicker"]))

    # name: 4 extruded layers under a gradient face, revealed left to right
    px, cols = pixels(cfg["name"].upper())
    p, y0 = 11, 102
    shades = ["#2e2610", "#4a3c17", "#6e5821", "#97782b"]
    layers = "".join(f'<path d="{block_path(px, X0, y0, p, k, k)}" fill="{c}"/>'
                     for k, c in zip((4, 3, 2, 1), shades))
    face = block_path(px, X0, y0, p)
    name_w = cols * p
    doc.define(f'<clipPath id="nameface"><path d="{face}"/></clipPath>'
               f'<clipPath id="reveal"><rect class="rv" x="{X0 - 2}" y="{y0 - 4}" width="{name_w + 10}" height="{7 * p + 12}"/></clipPath>')
    doc.style(
        f".rv{{transform-origin:{X0 - 2}px 0;animation:rv 1.5s steps({cols},end) .2s both}}"
        "@keyframes rv{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
        f".head{{opacity:0;animation:head 1.5s steps({cols},end) .2s}}"
        f"@keyframes head{{from{{opacity:1;transform:translateX(0)}}to{{opacity:1;transform:translateX({name_w}px)}}}}"
        ".sh{animation:sh 7s ease-in-out 2.2s infinite;transform:translateX(-260px)}"
        f"@keyframes sh{{0%{{transform:translateX(-260px)}}22%,100%{{transform:translateX({name_w + 300}px)}}}}"
    )
    doc.add(f'<g clip-path="url(#reveal)">{layers}<path d="{face}" fill="url(#face)"/>'
            f'<g clip-path="url(#nameface)"><g class="sh"><rect x="{X0}" y="{y0 - 10}" width="140" height="{7 * p + 20}" '
            f'fill="url(#shine)" transform="skewX(-18)"/></g></g></g>',
            f'<rect class="head" x="{X0 - 3}" y="{y0 - 6}" width="3" height="{7 * p + 12}" fill="#fff" filter="url(#glow)"/>')

    # role · city (sem japonês)
    y = 238
    doc.add(text(X0, y, cfg["role"], "gold2 b", 22))
    x = X0 + tw(cfg["role"], 22) + 24
    doc.add(rect(x, y - 13, 7, 7, FAINT))
    doc.add(text(x + 22, y - 2, cfg["location"], "mut", 16))

    # do pino ao servidor: nodes on a bus, a packet runs through and lights each one
    nodes = cfg["banner"]["path"]
    by, x1 = 284, W - X0
    step = (x1 - X0) / (len(nodes) - 1)
    travel, cycle = 4.6, 7.0
    doc.style(
        f".bus{{stroke-dasharray:90 {x1 - X0 + 200};stroke-dashoffset:90;animation:bus {cycle}s linear 1.8s infinite}}"
        f"@keyframes bus{{0%{{stroke-dashoffset:90}}{travel / cycle * 100:.1f}%,100%{{stroke-dashoffset:{-(x1 - X0)}}}}}"
        f".pk{{opacity:0;animation:pk {cycle}s linear 1.8s infinite}}"
        f"@keyframes pk{{0%{{opacity:1;transform:translateX(0)}}{travel / cycle * 100:.1f}%{{opacity:1;transform:translateX({x1 - X0}px)}}"
        f"{travel / cycle * 100 + 3:.1f}%,100%{{opacity:0;transform:translateX({x1 - X0}px)}}}}"
        f".nd{{animation:nd {cycle}s ease-out infinite}}"
        f"@keyframes nd{{0%,4%{{fill:{GOLD2}}}20%,100%{{fill:{BG}}}}}"
        f".nl{{fill:{DIM};animation:nl {cycle}s ease-out infinite}}"
        f"@keyframes nl{{0%,6%{{fill:{GOLD2}}}26%,100%{{fill:{DIM}}}}}"
    )
    doc.add(f'<path d="M{X0} {by + .5}H{x1}" stroke="{LN2}"/>',
            f'<path class="bus" d="M{X0} {by + .5}H{x1}" stroke="{GOLD}" stroke-width="2"/>')
    for i, name in enumerate(nodes):
        nx = X0 + i * step
        delay = 1.8 + travel * i / (len(nodes) - 1)
        anchor = "start" if i == 0 else "end" if i == len(nodes) - 1 else "middle"
        doc.add(f'<rect class="nd" x="{nx - 5:.1f}" y="{by - 4.5}" width="10" height="10" fill="{BG}" stroke="{GOLD}" '
                f'style="animation-delay:{delay:.2f}s"/>',
                f'<text class="lab nl" x="{nx - 5 if i == 0 else nx + 5 if i == len(nodes) - 1 else nx:.1f}" y="{by + 26}" '
                f'text-anchor="{anchor}" style="animation-delay:{delay:.2f}s">{esc(name.upper())}</text>')
    doc.add(f'<rect class="pk" x="{X0 - 4}" y="{by - 3.5}" width="8" height="8" fill="{GOLD2}" filter="url(#glow)"/>')

    # prompt
    doc.add(f'<path d="M0 {H - 72.5}H{W}" stroke="{LN}"/>')
    ty = H - 28
    prompt = [("okaru@lab", "jade"), (":", "dim"), ("~", "sky"), ("$ ", "dim")]
    pw = tw("".join(t for t, _ in prompt), 20)
    clip, css, body = typing(cfg["typing"], X0, ty, 20, pw)
    doc.define(clip).style(css).add(spans(X0, ty, prompt, 20), body)

    doc.add(rect(0, 0, W, H, "url(#scan)"), rect(.5, .5, W - 1, H - 1, "none", LN2))
    doc.save(path)
