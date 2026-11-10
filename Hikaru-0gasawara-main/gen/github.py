"""Everything the panels show about the GitHub account, fetched live.

With GITHUB_TOKEN (the Action always has one) the data comes from the GraphQL
API. Without a token, for local runs, it falls back to the public REST API
plus the public contribution calendar, which give the same numbers for public
activity.
"""

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request

API = "https://api.github.com"
UA = "hikaru-0gasawara-profile-renderer"

USER_Q = """
query($login: String!) {
  user(login: $login) {
    name login createdAt
    followers(first: 1) { totalCount }
    pullRequests(first: 1) { totalCount }
    issues(first: 1) { totalCount }
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes { ...repo }
    }
    contributionsCollection {
      totalCommitContributions
      contributionYears
    }
  }
}
fragment repo on Repository {
  name nameWithOwner description url isFork stargazerCount forkCount pushedAt
  primaryLanguage { name color }
  languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
}
"""

YEAR_Q = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""

REPO_Q = """
query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { ...repo } }
fragment repo on Repository {
  name nameWithOwner description url isFork stargazerCount forkCount pushedAt
  primaryLanguage { name color }
  languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
}
"""


def _req(url, token=None, body=None, accept="application/vnd.github+json"):
    headers = {"User-Agent": UA, "Accept": accept}
    if token:
        headers["Authorization"] = f"bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8")


def _gql(token, query, **variables):
    out = json.loads(_req(f"{API}/graphql", token, {"query": query, "variables": variables}))
    if out.get("errors"):
        raise RuntimeError(out["errors"][0].get("message", "graphql error"))
    return out["data"]


def _repo_from_gql(n):
    return {
        "name": n["name"], "full": n["nameWithOwner"], "desc": n["description"], "url": n["url"],
        "fork": n["isFork"], "stars": n["stargazerCount"], "forks": n["forkCount"],
        "pushed": (n["pushedAt"] or n.get("createdAt") or "1970-01-01")[:10],
        "lang": (n["primaryLanguage"] or {}).get("name"), "lang_color": (n["primaryLanguage"] or {}).get("color"),
        "languages": [(e["node"]["name"], e["node"]["color"], e["size"]) for e in n["languages"]["edges"]],
    }


def _years(created, today):
    return range(created.year, today.year + 1)


def fetch_graphql(login, token, extra_repos):
    u = _gql(token, USER_Q, login=login)["user"]
    created = dt.date.fromisoformat(u["createdAt"][:10])
    today = dt.datetime.now(dt.timezone.utc).date()
    calendar, commits_total = {}, 0
    for year in _years(created, today):
        c = _gql(token, YEAR_Q, login=login, **{"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"})
        c = c["user"]["contributionsCollection"]
        commits_total += c["totalCommitContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                calendar[d["date"]] = d["contributionCount"]
    extra = {}
    for full in extra_repos:
        owner, name = full.split("/")
        try:
            extra[full] = _repo_from_gql(_gql(token, REPO_Q, owner=owner, name=name)["repository"])
        except Exception as exc:
            print(f"  ! could not read {full}: {exc}")
    return {
        "login": u["login"], "name": u["name"], "created": created,
        "followers": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"], "issues": u["issues"]["totalCount"],
        "contributed_to": u["repositoriesContributedTo"]["totalCount"],
        "commits_year": u["contributionsCollection"]["totalCommitContributions"],
        "commits_total": commits_total,
        "repos": [_repo_from_gql(n) for n in u["repositories"]["nodes"]],
        "calendar": calendar, "extra": extra, "source": "graphql",
    }


# --- public fallback -------------------------------------------------------

def _rest(path):
    return json.loads(_req(API + path))


def _search_count(q):
    return _rest("/search/" + q)["total_count"]


def _scrape_year(login, year):
    page = _req(f"https://github.com/users/{login}/contributions?from={year}-01-01&to={year}-12-31",
                accept="text/html")
    ids = {cell_id: date for date, cell_id in re.findall(r'data-date="([\d-]+)" id="([^"]+)"', page)}
    days = {}
    for cell_id, tip in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        if cell_id in ids:
            m = re.match(r"([\d,]+) contributions?", tip)
            days[ids[cell_id]] = int(m.group(1).replace(",", "")) if m else 0
    return days


def _repo_from_rest(r):
    langs = _rest(f"/repos/{r['full_name']}/languages")
    return {
        "name": r["name"], "full": r["full_name"], "desc": r["description"], "url": r["html_url"],
        "fork": r["fork"], "stars": r["stargazers_count"], "forks": r["forks_count"],
        "pushed": r["pushed_at"][:10], "lang": r["language"], "lang_color": None,
        "languages": [(k, None, v) for k, v in langs.items()],
    }


def fetch_public(login, extra_repos):
    u = _rest(f"/users/{login}")
    created = dt.date.fromisoformat(u["created_at"][:10])
    today = dt.datetime.now(dt.timezone.utc).date()
    calendar = {}
    for year in _years(created, today):
        calendar.update(_scrape_year(login, year))
    since = (today - dt.timedelta(days=365)).isoformat()
    repos = [_repo_from_rest(r) for r in _rest(f"/users/{login}/repos?per_page=100&type=owner&sort=pushed")]
    extra = {}
    for full in extra_repos:
        try:
            extra[full] = _repo_from_rest(_rest(f"/repos/{full}"))
        except Exception as exc:
            print(f"  ! could not read {full}: {exc}")
    q = urllib.parse.quote
    return {
        "login": u["login"], "name": u["name"], "created": created,
        "followers": u["followers"],
        "prs": _search_count(f"issues?q={q(f'author:{login} type:pr')}"),
        "issues": _search_count(f"issues?q={q(f'author:{login} type:issue')}"),
        "contributed_to": None,
        "commits_year": _search_count(f"commits?q={q(f'author:{login} author-date:>={since}')}"),
        "commits_total": _search_count(f"commits?q={q(f'author:{login}')}"),
        "repos": repos, "calendar": calendar, "extra": extra, "source": "public",
    }


# --- derived numbers --------------------------------------------------------

LINGUIST_COLORS = {  # used when the REST fallback gives names without colors
    "Python": "#3572A5", "Java": "#b07219", "C": "#555555", "C++": "#f34b7d", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "PowerShell": "#012456",
    "Jupyter Notebook": "#DA5B0B", "SQL": "#e38c00", "MicroPython": "#3572A5", "SCSS": "#c6538c",
    "Batchfile": "#C1F12E", "Dockerfile": "#384d54", "Vue": "#41b883", "Kotlin": "#A97BFF",
}


def derive(d, skip_repos=()):
    """Totals shared by several panels."""
    today = dt.datetime.now(dt.timezone.utc).date()
    own = [r for r in d["repos"] if not r["fork"] and r["name"] not in skip_repos]
    d["own"] = own
    d["repo_count"] = len([r for r in d["repos"] if not r["fork"]])
    d["stars"] = sum(r["stars"] for r in d["repos"] if not r["fork"])
    # languages weighted like github-readme-stats with size_weight=count_weight=0.5,
    # so one big repo doesn't drown out everything else
    size, count, color = {}, {}, {}
    for r in own:
        for name, col, n in r["languages"]:
            size[name] = size.get(name, 0) + n
            count[name] = count.get(name, 0) + 1
            color[name] = col or color.get(name) or LINGUIST_COLORS.get(name, "#A3AD9F")
    score = {k: (size[k] ** 0.5) * (count[k] ** 0.5) for k in size}
    total = sum(score.values()) or 1
    d["languages"] = sorted(((k, color[k], score[k] / total, size[k], count[k]) for k in score),
                            key=lambda t: -t[2])
    cal = {dt.date.fromisoformat(k): v for k, v in d["calendar"].items()}
    cal = {k: v for k, v in cal.items() if k <= today}
    d["cal"] = cal
    d["today"] = today
    d["contrib_total"] = sum(cal.values())
    d["contrib_year"] = sum(v for k, v in cal.items() if (today - k).days < 365)
    d["active_days_year"] = sum(1 for k, v in cal.items() if (today - k).days < 365 and v)
    # streaks: today without contributions doesn't break the current streak yet
    longest, run, run_start, best = 0, 0, None, (None, None)
    day = min(cal, default=today)
    while day <= today:  # walk every date: a missing day counts as zero
        if cal.get(day):
            if run == 0:
                run_start = day
            run += 1
            if run > longest:
                longest, best = run, (run_start, day)
        else:
            run = 0
        day += dt.timedelta(days=1)
    cur, end = 0, today if cal.get(today) else today - dt.timedelta(days=1)
    day = end
    while cal.get(day):
        cur += 1
        day -= dt.timedelta(days=1)
    d["streak_cur"] = cur
    d["streak_cur_range"] = (day + dt.timedelta(days=1), end) if cur else (None, None)
    d["streak_best"] = longest
    d["streak_best_range"] = best
    first = min((k for k, v in cal.items() if v), default=d["created"])
    d["first_contrib"] = first
    return d


def fetch(login, extra_repos=(), skip_repos=()):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    data = None
    if token:
        try:
            data = fetch_graphql(login, token, extra_repos)
        except Exception as exc:
            print(f"  ! GraphQL failed ({exc}); falling back to public endpoints")
    if data is None:
        data = fetch_public(login, extra_repos)
    print(f"  data via {data['source']}: {len(data['repos'])} repos, {len(data['calendar'])} calendar days")
    return derive(data, skip_repos)
