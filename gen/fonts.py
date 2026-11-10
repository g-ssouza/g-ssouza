"""Embeds subsetted web fonts straight into each SVG.

GitHub serves README images as <img>, which can't load external fonts, but a
data: URI inside the SVG's own <style> works. Google Fonts' `text=` parameter
returns a font holding only the glyphs we ask for, so each panel carries a few
KB of font instead of the whole family. If the network is down the SVGs still
render with the monospace fallback stack.
"""

import base64
import hashlib
import os
import re
import urllib.parse
import urllib.request

CACHE = os.path.join(os.path.dirname(__file__), ".cache", "fonts")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

# alias used in our CSS -> Google Fonts family spec
FAMILIES = {
    "JBM": "JetBrains Mono:wght@400..800",
    "DG": "DotGothic16",
}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def face(alias, chars):
    """@font-face rule for `alias` holding just `chars`, or '' if unavailable."""
    chars = "".join(sorted(set(chars) - {"\n", "\r", "\t"}))
    if not chars.strip():
        return ""
    family = FAMILIES[alias]
    key = hashlib.sha1((family + "\0" + chars).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{alias}-{key}.woff2")
    if not os.path.exists(path):
        try:
            css = _get("https://fonts.googleapis.com/css2?" + urllib.parse.urlencode(
                {"family": family, "text": chars, "display": "block"})).decode()
            url = re.search(r"url\((.*?)\)", css).group(1)
            data = _get(url)
        except Exception as exc:  # offline or API change: fall back to system fonts
            print(f"  ! font {alias} unavailable ({exc.__class__.__name__}), using fallback")
            return ""
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    weight = "font-weight:400 800;" if alias == "JBM" else ""
    return f"@font-face{{font-family:'{alias}';{weight}src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
