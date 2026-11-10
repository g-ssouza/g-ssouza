"""python -m gen  →  renders every panel into assets/.

Options:
  --only banner,fetch   render just these scenes
  --cache FILE          reuse fetched GitHub data from FILE (written on first run);
                        handy while tweaking visuals without hitting the API
"""

import argparse
import datetime as dt
import importlib
import json
import os

from . import github

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

SCENES = ["banner", "buttons", "fetch", "loadout", "projects", "stats", "langs", "streak",
          "activity", "trophies", "snake", "footer"]


def load_data(cfg, cache):
    extra = [p["repo"] for p in cfg["projects"] + [cfg["portfolio_card"]]
             if p.get("repo") and not p["repo"].startswith(cfg["login"] + "/")]
    if cache and os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            raw = json.load(f)
        raw["created"] = dt.date.fromisoformat(raw["created"])
        print(f"  data from cache {cache}")
        return github.derive(raw, cfg["skip_repos"])
    data = github.fetch(cfg["login"], extra, cfg["skip_repos"])
    if cache:
        raw = {k: data[k] for k in ("login", "name", "created", "followers", "prs", "issues", "contributed_to",
                                    "commits_year", "commits_total", "repos", "calendar", "extra", "source")}
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(raw, f, default=str, indent=1)
    return data


def main():
    ap = argparse.ArgumentParser(prog="gen")
    ap.add_argument("--only")
    ap.add_argument("--cache")
    args = ap.parse_args()
    with open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(ASSETS, exist_ok=True)
    data = load_data(cfg, args.cache)
    for name in (args.only.split(",") if args.only else SCENES):
        mod = importlib.import_module(f".scenes.{name}", __package__)
        mod.render(cfg, data, os.path.join(ASSETS, f"{name}.svg"))


if __name__ == "__main__":
    main()
