"""Cards de projetos gerados automaticamente a partir dos repositórios públicos.

A lista vem da API do GitHub (data["own"]). Se existir entrada em cfg["projects"]
com o mesmo repo, usa título/descrição/stack customizados.
"""

import datetime as dt
import os
import re

from ..github import LINGUIST_COLORS
from ..svg import (BG, DIM, FAINT, GOLD, GOLD2, LN, LN2, PN2, Doc, date_en, icon, panel, rect, side_pad, spans,
                   text, tw, wrap)

W, H = 495, 258

# ícone padrão por linguagem
LANG_ICON = {
    "Java": ("springboot", "#6DB33F"),
    "HTML": ("html5", "#E34F26"),
    "CSS": ("filter", "#264DE4"),
    "Python": ("python", "#5A9BD0"),
    "TypeScript": ("typescript", "#4A90E2"),
    "JavaScript": ("typescript", "#F0CE6A"),
    "C++": ("cplusplus", "#5B9BD5"),
    "C": ("cplusplus", "#5B9BD5"),
}
DEFAULT_ICON = ("chip", "#F0CE6A")


def when(iso):
    try:
        return date_en(dt.date.fromisoformat(iso[:10]))
    except Exception:
        return iso[:10] if iso else "—"


def repo_info(data, full):
    if not full:
        return None
    for r in data.get("repos", []):
        if r.get("full") == full or r.get("name") == full.split("/")[-1]:
            return r
    return data.get("extra", {}).get(full)


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
        out.append(spans(x, fy, [("★ ", "gold"), (str(info.get("stars", 0)), "mut")], 12))
        x += tw(f"★ {info.get('stars', 0)}", 12) + 18
        if info.get("pushed"):
            out.append(spans(x, fy, [("atualizado ", "dim"), (when(info["pushed"]), "mut")], 12))
    else:
        out.append(text(16, fy, "repositório público", "ft dim"))
    out.append(text(W - 16, fy, link_text, "ft gold2", anchor="end"))
    return "".join(out)


def card(p, info, path, side):
    doc = Doc(W, H, f"{p['title']} — {p.get('tags', '')}", p.get("line", ""), pad=side_pad(side))
    doc.style(".chip{fill:#C9CBBE}.ft{font-size:12px}.ds{font-size:13.5px}")
    doc.add(panel(0, 0, W, H, f"{p['num']} · {p.get('tags', 'repo')}", p.get("period", "público")))
    doc.add(rect(16.5, 50.5, 43, 43, PN2, "rgba(216,178,74,.42)"),
            icon(p["icon"], 25, 59, 26, p["color"]))
    doc.add(text(74, 70, p["title"], "tx b", 22))
    subtitle = info["full"] if info and info.get("full") else (info["name"] if info else "")
    doc.add(text(74, 90, subtitle or "projeto", "dim", 11.5))
    desc = p.get("line") or (info.get("desc") if info else "") or "Repositório público no GitHub."
    lines = wrap(desc, int((W - 32) / (13.5 * .6)))[:4]
    for k, ln in enumerate(lines):
        doc.add(text(16, 124 + k * 20, ln, "ds mut"))
    stack = p.get("stack") or []
    if not stack and info:
        stack = [n for n, _, _ in (info.get("languages") or [])[:4]]
        if not stack and info.get("lang"):
            stack = [info["lang"]]
    doc.add(chips(16, 124 + 4 * 20 - 6, stack, 11, max_x=W - 16))
    doc.add(footer(H - 36, info, "abrir repositório →" if info else "ver no GitHub →"))
    doc.save(path)


def _slug(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "repo"


def _build_projects(cfg, data):
    """Lista automática a partir dos repos públicos + overrides do config."""
    skip = set(cfg.get("skip_repos") or [])
    login = cfg.get("login", "")
    skip.add(login)

    # overrides por nome do repo ou full name
    overrides = {}
    for p in cfg.get("projects") or []:
        repo = p.get("repo") or ""
        key = repo.split("/")[-1] if repo else p.get("id", "")
        if key:
            overrides[key.lower()] = p

    own = data.get("own") or [
        r for r in data.get("repos", [])
        if not r.get("fork") and r.get("name") not in skip
    ]
    # ordenar por push mais recente
    own = sorted(own, key=lambda r: r.get("pushed") or "", reverse=True)

    projects = []
    for i, r in enumerate(own[:8]):  # no máximo 8 cards
        name = r.get("name") or f"repo-{i+1}"
        ov = overrides.get(name.lower(), {})
        lang = r.get("lang") or (r.get("languages") or [[None]])[0][0]
        icon_name, color = LANG_ICON.get(lang, DEFAULT_ICON)
        if ov.get("icon"):
            icon_name = ov["icon"]
        if ov.get("color"):
            color = ov["color"]

        stack = ov.get("stack")
        if not stack:
            stack = [n for n, _, _ in (r.get("languages") or [])[:4]]
            if not stack and lang:
                stack = [lang]

        title = ov.get("title") or name.replace("-", " ").replace("_", " ")
        line = ov.get("line") or r.get("desc") or "Repositório público no GitHub."
        tags = ov.get("tags") or (lang.lower() if lang else "repo")
        period = ov.get("period") or "público"
        full = r.get("full") or f"{login}/{name}"

        projects.append({
            "id": f"{i+1:02d}",
            "num": f"{i+1:02d}",
            "title": title[:40],
            "tags": tags,
            "period": period,
            "icon": icon_name,
            "color": color,
            "line": line[:200],
            "stack": stack[:5],
            "repo": full,
            "_info": r,
        })
    return projects


def _update_readme(projects, login):
    """Reescreve a seção de projetos no README.md com os SVGs gerados."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    readme = os.path.join(root, "README.md")
    if not os.path.exists(readme):
        return

    text = open(readme, encoding="utf-8").read()

    # montar HTML dos cards (2 por linha)
    rows = []
    for i in range(0, len(projects), 2):
        chunk = projects[i:i+2]
        cells = []
        for p in chunk:
            href = f"https://github.com/{p['repo']}" if p.get("repo") else f"https://github.com/{login}"
            cells.append(
                f'<a href="{href}"><img src="assets/project-{p["id"]}.svg" width="50%" alt="{p["title"]}"></a>'
            )
        rows.append("<p align=\"center\">\n  " + "".join(cells) + "\n</p>")

    if not rows:
        rows = ['<p align="center"><em>Nenhum repositório público ainda.</em></p>']

    block = (
        "### `$ ls ~/projects` &nbsp;·&nbsp; projetos\n\n"
        + "\n".join(rows)
        + "\n"
    )

    pattern = re.compile(
        r"### `\$ ls ~/projects`.*?projetos\n\n.*?(?=\n### |\n<p align=\"center\">\s*\n  <img src=\"assets/footer)",
        re.DOTALL,
    )
    if pattern.search(text):
        text = pattern.sub(block + "\n", text)
    else:
        # fallback: substitui entre projects e gh status
        pattern2 = re.compile(
            r"### `\$ ls ~/projects`.*?(?=### `\$ gh status`)",
            re.DOTALL,
        )
        if pattern2.search(text):
            text = pattern2.sub(block + "\n", text)
        else:
            print("  ! não consegui atualizar a seção de projetos no README")
            return

    open(readme, "w", encoding="utf-8").write(text)
    print(f"  README: {len(projects)} projeto(s) automático(s)")


def render(cfg, data, path):
    out = os.path.dirname(path)
    projects = _build_projects(cfg, data)

    # limpar SVGs antigos de projetos
    for name in os.listdir(out):
        if name.startswith("project-") and name.endswith(".svg"):
            try:
                os.remove(os.path.join(out, name))
            except OSError:
                pass

    for i, p in enumerate(projects):
        info = p.pop("_info", None) or repo_info(data, p.get("repo"))
        card(p, info, os.path.join(out, f"project-{p['id']}.svg"), ("left", "right")[i % 2])

    _update_readme(projects, cfg.get("login", ""))
    # path é assets/projects.svg — não usamos arquivo único; criamos um stub vazio ok
    open(path, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><title>{len(projects)} projects</title></svg>\n'
    )
    print(f"  {len(projects)} project card(s)")
