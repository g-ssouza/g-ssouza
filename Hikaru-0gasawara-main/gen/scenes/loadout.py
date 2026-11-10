"""Tech stack as the portfolio's RPG loadout: eight equipped slots (the selection
cycles through them, the detail box follows) and the backpack grid."""

from ..svg import GOLD, GOLD2, LN, LN2, PN2, Doc, icon, label, panel, rect, text, wrap

W, H = 1000, 412
STEP = 3  # seconds each equipped item stays selected


def render(cfg, data, path):
    equip, bag = cfg["equip"], cfg["bag"]
    n = len(equip)
    doc = Doc(W, H, "Stack — equipped and backpack",
              "Equipped: " + ", ".join(e["name"] for e in equip) + ". Backpack: "
              + "; ".join(f"{k}: {v}" for k, v in cfg["bag_text"]) + ".")
    doc.define('<radialGradient id="slot" cx=".5" cy=".4" r=".64"><stop offset="0" stop-color="#D8B24A" stop-opacity=".10"/>'
               '<stop offset="1" stop-color="#D8B24A" stop-opacity="0"/></radialGradient>'
               '<radialGradient id="slotOn" cx=".5" cy=".4" r=".66"><stop offset="0" stop-color="#D8B24A" stop-opacity=".24"/>'
               '<stop offset="1" stop-color="#D8B24A" stop-opacity="0"/></radialGradient>'
               '<pattern id="bagGrid" width="58" height="58" patternUnits="userSpaceOnUse">'
               '<path d="M58 0V58M0 58H58" stroke="rgba(232,228,212,.07)"/></pattern>')
    doc.style(
        f".sel{{opacity:0;animation:sel {n * STEP}s steps(1,end) infinite}}.sel0{{opacity:1}}"
        f"@keyframes sel{{0%{{opacity:1}}{100 / n:.3f}%,100%{{opacity:0}}}}"
        ".en{font-size:9.5px;letter-spacing:.8px}"
        ".dn{font-size:15px}.du{font-size:12px}.df{font-size:12px;font-style:italic}"
        ".bt{font-size:11px}"
        f".ping{{opacity:0;animation:ping {len(bag) * 0.6:.1f}s linear infinite}}"
        f"@keyframes ping{{0%{{opacity:1}}{100 / len(bag) * 2:.2f}%,100%{{opacity:0}}}}"
    )

    # --- equipped -----------------------------------------------------------
    lw = 490
    doc.add(panel(0, 0, lw, H, "Equipped", "daily use"))
    size, gap = 106, 8
    gx = (lw - (4 * size + 3 * gap)) / 2
    gy = 50
    for i, e in enumerate(equip):
        x = gx + (i % 4) * (size + gap)
        y = gy + (i // 4) * (size + gap)
        delay = f' style="animation-delay:{i * STEP}s"'
        cls = "sel sel0" if i == 0 else "sel"
        doc.add(rect(x + .5, y + .5, size - 1, size - 1, PN2, "rgba(216,178,74,.42)"),
                rect(x + 1, y + 1, size - 2, size - 2, "url(#slot)"),
                f'<g class="{cls}"{delay}>{rect(x + .5, y + .5, size - 1, size - 1, "url(#slotOn)", GOLD2)}'
                f'{rect(x - 1.5, y - 1.5, size + 3, size + 3, "none", "rgba(240,206,106,.25)")}</g>',
                icon(e["icon"], x + size / 2 - 17, y + 24, 34, e["color"]),
                text(x + size / 2, y + 84, e["short"].upper(), "en mut", anchor="middle"),
                f'<g class="{cls}"{delay}>{text(x + size / 2, y + 84, e["short"].upper(), "en gold2", anchor="middle")}</g>')

    # detail box: one group per item, shown while that item is selected
    by = gy + 2 * size + gap + 14
    bh = H - by - 14
    doc.add(rect(gx + .5, by + .5, lw - 2 * gx - 1, bh - 1, "rgba(0,0,0,.25)", LN))
    tx, tr = gx + 14, lw - gx - 14
    for i, e in enumerate(equip):
        cls = "sel sel0" if i == 0 else "sel"
        lines = wrap(e["use"], int((tr - tx) / (12 * .6)))[:2]
        parts = [text(tx, by + 30, e["name"], "dn tx b"),
                 label(tr, by + 29, f"{e['slot']} · {e['type']}", "gold", anchor="end")]
        parts += [text(tx, by + 56 + k * 18, ln, "du mut") for k, ln in enumerate(lines)]
        if e.get("flavor"):
            parts.append(text(tx, by + 64 + len(lines) * 18, e["flavor"], "df gold"))
        doc.add(f'<g class="{cls}" style="animation-delay:{i * STEP}s">{"".join(parts)}</g>')

    # --- backpack -----------------------------------------------------------
    rx, rw = lw + 12, W - lw - 12
    doc.add(panel(rx, 0, rw, H, "Backpack", f"{len(bag)} items"))
    cell = 58
    bx = rx + (rw - 8 * cell) / 2
    byy = 50
    doc.add(rect(bx + .5, byy + .5, 8 * cell - 1, 4 * cell - 1, "rgba(0,0,0,.28)", LN2),
            rect(bx, byy, 8 * cell, 4 * cell, "url(#bagGrid)"))
    for j, (name, color, c, r, w, h) in enumerate(bag):
        x, y = bx + (c - 1) * cell + 2, byy + (r - 1) * cell + 2
        iw, ih = w * cell - 4, h * cell - 4
        big = w > 1 and h > 1
        s = 34 if big else 22
        doc.add(rect(x + .5, y + .5, iw - 1, ih - 1, "rgba(19,27,21,.94)", LN2),
                f'<g class="ping" style="animation-delay:{j * 0.6:.1f}s">'
                f'{rect(x + .5, y + .5, iw - 1, ih - 1, "rgba(216,178,74,.1)", GOLD)}</g>',
                icon(name, x + iw / 2 - s / 2, y + ih / 2 - s / 2, s, color, sw=1.8))

    ty = byy + 4 * cell + 28
    for k, (lab_, val) in enumerate(cfg["bag_text"]):
        doc.add(label(bx, ty + k * 18, lab_), text(bx + 92, ty + k * 18, val, "bt mut"))
    doc.save(path)
