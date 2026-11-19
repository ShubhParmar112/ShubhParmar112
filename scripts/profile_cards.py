"""Build the contribution heatmap and the stats card from the GitHub GraphQL API.

Standard library only, so the workflow needs no `pip install`. Writes two
self-contained SVGs that match the palette used by the rest of the profile.

    GITHUB_TOKEN=... python scripts/profile_cards.py --login ShubhParmar112 --out cards

Only public activity is counted: that is all the API exposes to a token with
`public_repo` scope, and the README says as much.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.github.com/graphql"

# --- palette (shared with assets/*.svg) -------------------------------------
BG_A, BG_B = "#0A0F1E", "#101A33"
BORDER, TEXT, MUTED, DIM = "#223055", "#E8EEF9", "#8FA3C8", "#5E7299"
BLUE, TEAL, AMBER = "#4F9CF9", "#2DD4BF", "#F5A524"
LEVELS = ["#15203A", "#164A72", "#1C7FA8", "#25B3C4", "#2DD4BF"]

FONT = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    name
    login
    followers { totalCount }
    contributionsCollection(from:$from, to:$to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false,
                 orderBy:{field:STARGAZERS, direction:DESC}) {
      totalCount
      nodes {
        stargazerCount
        forkCount
        languages(first:8, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


# --- helpers ----------------------------------------------------------------
def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def count(n, singular, plural=None):
    """'1 PR', '2 PRs' — the footer reads wrong without this."""
    word = singular if n == 1 else (plural or singular + "s")
    return "{:,} {}".format(n, word)


def fetch(login, token):
    to = datetime.now(timezone.utc).replace(microsecond=0)
    frm = to - timedelta(days=364)
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
            "from": frm.isoformat().replace("+00:00", "Z"),
            "to": to.isoformat().replace("+00:00", "Z"),
        },
    }).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": "profile-cards-script",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit("GraphQL error: {}".format(payload["errors"]))
    return payload["data"]["user"]


def level_of(count, peak):
    if count <= 0:
        return 0
    if peak <= 4:
        return min(4, count)
    share = count / peak
    for idx, cut in enumerate((0.15, 0.35, 0.60), start=1):
        if share <= cut:
            return idx
    return 4


def streaks(days):
    """Current and longest streak over the window, ignoring an empty today."""
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    tail = counts[:-1] if counts and counts[-1] == 0 else counts
    current = 0
    for c in reversed(tail):
        if c > 0:
            current += 1
        else:
            break
    return current, longest


def card_shell(width, height, title, subtitle, uid):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        'width="{w}" height="{h}" role="img" aria-label="{a}">'.format(
            w=width, h=height, a=esc(subtitle)),
        "  <title>{}</title>".format(esc(subtitle)),
        "  <defs>",
        '    <linearGradient id="bg{u}" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="{a}"/>'
        '<stop offset="100%" stop-color="{b}"/></linearGradient>'.format(u=uid, a=BG_A, b=BG_B),
        '    <linearGradient id="rule{u}" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="{bl}" stop-opacity="0.9"/>'
        '<stop offset="100%" stop-color="{tl}" stop-opacity="0"/></linearGradient>'.format(
            u=uid, bl=BLUE, tl=TEAL),
        "  </defs>",
        '  <rect width="{w}" height="{h}" rx="14" fill="url(#bg{u})"/>'.format(
            w=width, h=height, u=uid),
        '  <rect x="0.5" y="0.5" width="{w}" height="{h}" rx="14" '
        'fill="none" stroke="{b}"/>'.format(w=width - 1, h=height - 1, b=BORDER),
        '  <text x="26" y="40" font-family="{f}" font-size="19" font-weight="600" '
        'fill="{c}">{t}</text>'.format(f=FONT, c=TEXT, t=esc(title)),
        '  <rect x="26" y="52" width="120" height="2" rx="1" fill="url(#rule{u})"/>'.format(u=uid),
    ]


# --- heatmap ----------------------------------------------------------------
def build_heatmap(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    total = cal["totalContributions"]
    days = [d for w in weeks for d in w["contributionDays"]]
    peak = max((d["contributionCount"] for d in days), default=0)

    cell, gap = 12, 3
    step = cell + gap
    pad, label_w, grid_top = 26, 30, 92
    width = pad * 2 + label_w + len(weeks) * step
    height = grid_top + 7 * step + 62

    out = card_shell(
        width, height, "Contributions",
        "GitHub contribution heatmap: {:,} contributions in the last 12 months".format(total),
        "h")
    out.append(
        '  <text x="{x}" y="40" text-anchor="end" font-family="{f}" font-size="15" fill="{m}">'
        '<tspan fill="{t}" font-weight="600" font-size="17">{n:,}</tspan>'
        ' contribution{s} &#183; last 12 months</text>'.format(
            x=width - 26, f=FONT, m=MUTED, t=TEAL, n=total,
            s="" if total == 1 else "s"))

    # month labels
    seen = set()
    for wi, week in enumerate(weeks):
        first = week["contributionDays"][0]
        month = datetime.strptime(first["date"], "%Y-%m-%d").month
        if month not in seen and int(first["date"][8:10]) <= 7:
            seen.add(month)
            x = pad + label_w + wi * step
            if x < width - pad - 24:
                out.append(
                    '  <text x="{x}" y="{y}" font-family="{f}" font-size="12.5" '
                    'fill="{d}">{m}</text>'.format(
                        x=x, y=grid_top - 10, f=FONT, d=DIM, m=MONTHS[month - 1]))

    # weekday labels
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            '  <text x="{x}" y="{y}" font-family="{f}" font-size="11.5" '
            'fill="{d}">{n}</text>'.format(
                x=pad, y=grid_top + wd * step + cell - 2, f=FONT, d=DIM, n=name))

    # cells
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = pad + label_w + wi * step
            y = grid_top + day["weekday"] * step
            lvl = level_of(day["contributionCount"], peak)
            delay = (wi * 7 + day["weekday"]) * 0.0016
            out.append(
                '  <rect x="{x}" y="{y}" width="{c}" height="{c}" rx="2.5" fill="{col}" opacity="0">'
                '<title>{date}: {n} contributions</title>'
                '<animate attributeName="opacity" from="0" to="1" dur="0.45s" '
                'begin="{d:.3f}s" fill="freeze"/></rect>'.format(
                    x=x, y=y, c=cell, col=LEVELS[lvl], date=day["date"],
                    n=day["contributionCount"], d=delay))

    # legend
    ly = grid_top + 7 * step + 26
    lx = width - pad - 5 * 17 - 74
    out.append('  <text x="{x}" y="{y}" font-family="{f}" font-size="12" '
               'fill="{d}">Less</text>'.format(x=lx - 42, y=ly + 10, f=FONT, d=DIM))
    for i, colour in enumerate(LEVELS):
        out.append('  <rect x="{x}" y="{y}" width="12" height="12" rx="2.5" '
                   'fill="{c}"/>'.format(x=lx + i * 17, y=ly, c=colour))
    out.append('  <text x="{x}" y="{y}" font-family="{f}" font-size="12" '
               'fill="{d}">More</text>'.format(x=lx + 5 * 17 + 6, y=ly + 10, f=FONT, d=DIM))
    out.append(
        '  <text x="{x}" y="{y}" font-family="{f}" font-size="12" fill="{d}">'
        'Rebuilt daily from the GitHub GraphQL API &#183; public activity only</text>'.format(
            x=pad, y=ly + 10, f=FONT, d=DIM))
    out.append("</svg>")
    return "\n".join(out)


# --- stats ------------------------------------------------------------------
def build_stats(user):
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    current, longest = streaks(days)
    repos = user["repositories"]["nodes"]
    stars = sum(r["stargazerCount"] for r in repos)
    forks = sum(r["forkCount"] for r in repos)

    sizes = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            colour = edge["node"]["color"] or BLUE
            entry = sizes.setdefault(name, [0, colour])
            entry[0] += edge["size"]
    ranked = sorted(sizes.items(), key=lambda kv: kv[1][0], reverse=True)[:6]
    total_size = sum(v[0] for _, v in ranked) or 1

    width, height = 877, 268
    out = card_shell(
        width, height, "GitHub at a glance",
        "GitHub statistics: contributions, streaks, repositories, stars and language mix",
        "s")

    tiles = [
        ("{:,}".format(cal["totalContributions"]), "Contributions", TEAL),
        ("{}".format(current), "Day streak", AMBER),
        ("{}".format(longest), "Longest streak", BLUE),
        ("{}".format(user["repositories"]["totalCount"]), "Public repos", TEAL),
        ("{}".format(stars), "Stars earned", AMBER),
        ("{}".format(user["followers"]["totalCount"]), "Followers", BLUE),
    ]
    for i, (value, label, colour) in enumerate(tiles):
        col, row = i % 3, i // 3
        x = 26 + col * 148
        y = 92 + row * 78
        out.append(
            '  <text x="{x}" y="{y}" font-family="{f}" font-size="31" font-weight="700" '
            'fill="{c}">{v}</text>'.format(x=x, y=y, f=FONT, c=colour, v=value))
        out.append(
            '  <text x="{x}" y="{y}" font-family="{f}" font-size="13" '
            'fill="{m}">{l}</text>'.format(x=x, y=y + 22, f=FONT, m=MUTED, l=label))

    # divider + second column
    out.append('  <rect x="474" y="80" width="1" height="{h}" fill="{b}"/>'.format(
        h=height - 112, b=BORDER))
    out.append(
        '  <text x="506" y="96" font-family="{f}" font-size="13.5" font-weight="600" '
        'letter-spacing="1.6" fill="{m}">LANGUAGE MIX</text>'.format(f=FONT, m=MUTED))

    bar_x, bar_y, bar_w = 506, 112, width - 506 - 26
    cursor = float(bar_x)
    for name, (size, colour) in ranked:
        seg = max(4.0, bar_w * size / total_size)
        out.append(
            '  <rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="11" fill="{c}">'
            '<title>{n}</title></rect>'.format(
                x=cursor, y=bar_y, w=seg, c=colour, n=esc(name)))
        cursor += seg

    for i, (name, (size, colour)) in enumerate(ranked):
        col, row = i % 2, i // 2
        x = bar_x + col * 176
        y = bar_y + 42 + row * 26
        pct = 100.0 * size / total_size
        out.append('  <circle cx="{cx}" cy="{cy}" r="5" fill="{c}"/>'.format(
            cx=x + 5, cy=y - 4, c=colour))
        out.append(
            '  <text x="{x}" y="{y}" font-family="{f}" font-size="13.5" fill="{t}">'
            '{n} <tspan fill="{d}">{p:.1f}%</tspan></text>'.format(
                x=x + 18, y=y, f=FONT, t=TEXT, n=esc(name), d=DIM, p=pct))

    footer = " &#183; ".join([
        count(cc["totalCommitContributions"], "commit"),
        count(cc["totalPullRequestContributions"], "PR"),
        count(cc["totalIssueContributions"], "issue"),
        count(forks, "fork"),
        "last 12 months",
    ])
    out.append(
        '  <text x="26" y="{y}" font-family="{f}" font-size="12" fill="{d}">'
        '{t}</text>'.format(y=height - 20, f=FONT, d=DIM, t=footer))
    out.append("</svg>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=os.environ.get("GH_LOGIN", "ShubhParmar112"))
    ap.add_argument("--out", default="cards")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set", file=sys.stderr)
        return 1

    try:
        user = fetch(args.login, token)
    except urllib.error.HTTPError as exc:
        print("GitHub API returned {}: {!r}".format(exc.code, exc.read()[:400]), file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "heatmap.svg").write_text(build_heatmap(user), encoding="utf-8")
    (out_dir / "stats.svg").write_text(build_stats(user), encoding="utf-8")
    print("wrote {} and {}".format(out_dir / "heatmap.svg", out_dir / "stats.svg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
