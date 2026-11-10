"""Footer: the portfolio's CONTINUE? screen counting down beside a coin slot;
when it hits 0, GAME OVER drops in with the score (all-time contributions),
then the cycle starts again. Plus the render stamp."""

import datetime as dt

from ..svg import GOLD2, LN, RED, Doc, panel, rect, spans, text, tw
from .stats import level

W, H = 1000, 176
COUNT = 10      # seconds of countdown, 9 → 0
CYCLE = 16      # countdown plus the GAME OVER screen

COIN = [  # 10×10
    "...####...",
    ".##$$$$##.",
    ".#$$##$$#.",
    "#$$#$$#$$#",
    "#$$#$$$$$#",
    "#$$#$$$$$#",
    "#$$#$$#$$#",
    ".#$$##$$#.",
    ".##$$$$##.",
    "...####...",
]


def coin(x, y, s):
    cols = {"#": "#8A6A1E", "$": GOLD2}
    return "".join(rect(x + c * s, y + r * s, s, s, cols[ch])
                   for r, line in enumerate(COIN) for c, ch in enumerate(line) if ch in cols)


def render(cfg, data, path):
    now = dt.datetime.now(dt.timezone.utc)
    score = data["contrib_total"]
    lv = level(score)[0]
    doc = Doc(W, H, "Thanks for playing",
              f"Footer: CONTINUE? counts down from 9; at 0 it's GAME OVER, score {score}. Rendered {now:%Y-%m-%d %H:%M} UTC.")

    def pct(sec):
        return f"{sec / CYCLE * 100:.3f}%"

    doc.style(
        # CONTINUE? screen for the countdown, then GAME OVER until the cycle restarts
        f".cont{{animation:cont {CYCLE}s steps(1,end) infinite}}"
        f"@keyframes cont{{0%{{opacity:1}}{pct(COUNT)},100%{{opacity:0}}}}"
        f".dg{{animation:cd {CYCLE}s steps(1,end) infinite;opacity:0}}.dg9{{opacity:1}}"
        f"@keyframes cd{{0%{{opacity:1}}{pct(1)},100%{{opacity:0}}}}"
        ".blink{animation:blink 1.1s steps(1,end) infinite}@keyframes blink{60%{opacity:0}}"
        ".spin{animation:spin 1.2s steps(4,end) infinite;transform-origin:905px 62px}"
        "@keyframes spin{50%{transform:scaleX(.25)}}"
        f".flash{{opacity:0;animation:flash {CYCLE}s linear infinite}}"
        f"@keyframes flash{{0%,{pct(COUNT - .01)}{{opacity:0}}{pct(COUNT)}{{opacity:.3}}{pct(COUNT + .35)},100%{{opacity:0}}}}"
        f".score{{opacity:0;animation:late {CYCLE}s steps(1,end) infinite}}"
        f"@keyframes late{{0%{{opacity:0}}{pct(COUNT + 1.1)}{{opacity:1}}{pct(CYCLE - .05)},100%{{opacity:0}}}}"
    )
    doc.add(panel(0, 0, W, H))

    # --- CONTINUE? ---------------------------------------------------------
    x, y = 40, 74
    cont = [text(x, y, "CONTINUE?", "jp gold2", 40)]
    cx = x + 40 * 0.5 * 9 + 26  # DotGothic16 Latin glyphs are half-width
    for i, d in enumerate(range(9, -1, -1)):
        cls = "dg dg9" if d == 9 else "dg"
        cont.append(f'<g class="{cls}" style="animation-delay:{i}s">{text(cx, y, str(d), "jp tx", 40)}</g>')
    thanks = cfg["footer"]["thanks"]
    cont += [spans(x + 2, y + 34, [(thanks, "mut"), ("  ·  ", "faint")], 13),
             text(x + 2 + tw(thanks + "  ·  ", 13), y + 34, "ありがとう", "jp mut", 14),
             f'<g class="spin">{coin(875, 32, 6)}</g>',
             text(905, 120, "INSERT COIN", "jp gold blink", 16, anchor="middle")]
    doc.add(f'<g class="cont">{"".join(cont)}</g>')

    # --- GAME OVER: letters drop in one by one, then the score -------------
    doc.add(rect(1, 1, W - 2, H - 42, RED, extra=' class="flash"'))
    word, size, step = "GAME OVER", 50, 34
    gx = W / 2 - (len(word) * step - (step - size * .5)) / 2
    for i, ch in enumerate(word):
        if ch == " ":
            continue
        t = COUNT + .25 + i * .09
        doc.style(f".go{i}{{opacity:0;animation:go{i} {CYCLE}s linear infinite}}"
                  f"@keyframes go{i}{{0%,{pct(t)}{{opacity:0;transform:translateY(-16px)}}"
                  f"{pct(t + .01)}{{opacity:1;transform:translateY(-16px)}}"
                  f"{pct(t + .2)}{{opacity:1;transform:translateY(0)}}"
                  f"{pct(CYCLE - .05)}{{opacity:1;transform:translateY(0)}}100%{{opacity:0}}}}")
        lx = gx + i * step
        doc.add(f'<g class="go{i}">{text(lx + 3, 83, ch, "jp red", size)}{text(lx, 80, ch, "jp gold2", size)}</g>')
    doc.add(f'<g class="score">'
            + spans(W / 2, 114, [("SCORE ", "dim"), (f"{score:06d}", "gold2"), ("   ·   ", "faint"),
                                 ("LV ", "dim"), (str(lv), "gold2"), ("   ·   ", "faint"),
                                 ("contributions are points", "mut")], 13, extra=' text-anchor="middle"')
            + "</g>")

    # render stamp
    doc.add(f'<path d="M1 {H - 40.5}H{W - 1}" stroke="{LN}"/>')
    stamp = [("rendered ", "faint"), (f"{now:%Y-%m-%d %H:%M} UTC", "dim"), (" · ", "faint"),
             ("refreshed every 3 hours by GitHub Actions", "dim"), (" · ", "faint"), ("just SVG, no JavaScript", "dim"),
             (" · ", "faint"), (cfg["footer"]["credits"], "gold")]
    doc.add(spans(20, H - 15, stamp, 11), text(W - 20, H - 15, "↑↑↓↓←→←→BA", "faint", 11, anchor="end"))
    doc.save(path)
