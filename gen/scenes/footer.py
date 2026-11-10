"""Footer simples em português, sem GAME OVER."""

import datetime as dt

from ..svg import Doc, panel, text, spans


W, H = 1000, 110


def render(cfg, data, path):
    now = dt.datetime.now(dt.timezone.utc)
    thanks = cfg["footer"].get("thanks", "obrigado por visitar")
    credits = cfg["footer"].get("credits", "feito com café e ctrl+z em São Paulo")

    doc = Doc(W, H, "Obrigado por visitar",
              f"Footer. Renderizado {now:%Y-%m-%d %H:%M} UTC.")
    doc.add(panel(0, 0, W, H))
    doc.add(text(500, 42, thanks, "gold2", 22, anchor="middle"))
    doc.add(text(500, 68, credits, "mut", 13, anchor="middle"))
    doc.add(spans(20, 96, [
        ("atualizado automaticamente a cada 3 horas", "faint"),
        (" · ", "faint"),
        ("só SVG, sem JavaScript", "dim"),
    ], 11))
    doc.add(text(980, 96, "gsouza@lab", "faint", 11, anchor="end"))
    doc.save(path)
