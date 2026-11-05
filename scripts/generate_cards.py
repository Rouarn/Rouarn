#!/usr/bin/env python3
"""Generate brand-native GitHub profile cards as local SVGs."""
import json, os, urllib.request, urllib.error
from datetime import date, timedelta
from html import escape
from pathlib import Path

LOGIN = os.environ.get("GITHUB_LOGIN", "Rouarn")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
OUT = Path(__file__).resolve().parents[1] / "assets" / "generated"
PROJECTS = OUT.parent / "projects"
OUT.mkdir(parents=True, exist_ok=True)
PROJECTS.mkdir(parents=True, exist_ok=True)

LIGHT = dict(bg="#F3F1EC", panel="#FAF9F5", ink="#171512", muted="#5E5A52", faint="#8C877D", line="#D8D4C8", accent="#46A6C6")
DARK = dict(bg="#121210", panel="#1A1916", ink="#F2EFE7", muted="#A8A399", faint="#6F6A61", line="#2A2824", accent="#74C7E0")
COLORS = ["#F0995F", "#5FBEDC", "#A27FC2", "#EDDF55", "#46A6C6", "#8C877D"]

def req(url, graphql=None):
    data = json.dumps(graphql).encode() if graphql else None
    r = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
        "User-Agent": "vakao-profile-cards", "Content-Type": "application/json",
    })
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())

def card(w, h, dark=False):
    c = DARK if dark else LIGHT
    return c, f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">
<style>
text {{ font-family: Archivo, Inter, "PingFang SC", "Noto Sans SC", sans-serif; }}
.mono {{ font-family: "SF Mono", Menlo, Consolas, monospace; letter-spacing: 1.5px; }}
</style>
<rect width="{w}" height="{h}" fill="{c['bg']}"/>
<g stroke="{c['line']}" stroke-width="1" opacity=".55">
{''.join(f'<path d="M0 {y}H{w}"/>' for y in range(0, h, 40))}
{''.join(f'<path d="M{x} 0V{h}"/>' for x in range(0, w, 40))}
</g>
'''

def save(name, svg):
    (OUT / name).write_text(svg, encoding="utf-8")

def footer(c, w, h, page):
    return f'<text x="28" y="{h-22}" class="mono" font-size="11" fill="{c["faint"]}">VAKAO / {page}</text>'

def stats_card(user, repos, stars, total_contrib, dark=False):
    c = LIGHT if not dark else DARK
    w, h = 840, 220
    c, s = card(w, h, dark)
    s += f'<text x="30" y="34" class="mono" font-size="11" fill="{c["faint"]}">VAKAO / GITHUB PROFILE</text>'
    s += f'<text x="30" y="72" font-size="28" font-weight="700" fill="{c["ink"]}">{escape(user.get("name") or user.get("login"))} <tspan fill="{c["faint"]}">/ {escape(LOGIN)}</tspan></text>'
    vals = [("PUBLIC REPOS", user.get("public_repos", len(repos))), ("FOLLOWERS", user.get("followers", 0)), ("STARS", stars), ("CONTRIBUTIONS", total_contrib)]
    x = 30; step = (w - 60) / len(vals)
    for i, (label, val) in enumerate(vals):
        s += f'<text x="{x + i*step}" y="132" font-size="40" font-weight="700" fill="{c["ink"]}">{val:,}</text>'
        s += f'<text x="{x + i*step}" y="158" class="mono" font-size="10" fill="{c["muted"]}">{label}</text>'
    s += f'<rect x="30" y="180" width="{w-60}" height="3" fill="{c["accent"]}" opacity=".65"/>'
    s += footer(c, w, h, "STATS") + '</svg>'
    return s

def languages_card(langs, dark=False):
    c = LIGHT if not dark else DARK
    w, h = 840, 300
    c, s = card(w, h, dark)
    s += f'<text x="30" y="34" class="mono" font-size="11" fill="{c["faint"]}">VAKAO / TOP LANGUAGES</text>'
    s += f'<text x="30" y="70" font-size="24" font-weight="700" fill="{c["ink"]}">主要语言</text>'
    total = sum(langs.values()) or 1
    items = list(langs.items())[:6]
    y = 104
    for i, (name, val) in enumerate(items):
        pct = val / total
        s += f'<text x="30" y="{y}" font-size="13" fill="{c["muted"]}">{escape(name)}</text>'
        s += f'<text x="{w-30}" y="{y}" text-anchor="end" font-size="13" fill="{c["faint"]}">{pct*100:.1f}%</text>'
        s += f'<rect x="30" y="{y+8}" width="{w-60}" height="7" rx="3.5" fill="{c["line"]}"/>'
        s += f'<rect x="30" y="{y+8}" width="{(w-60)*pct:.1f}" height="7" rx="3.5" fill="{COLORS[i%len(COLORS)]}"/>'
        y += 30
    s += footer(c, w, h, "LANGUAGES") + '</svg>'
    return s

def streak_card(current, longest, total, dark=False):
    c = LIGHT if not dark else DARK
    w, h = 840, 220
    c, s = card(w, h, dark)
    s += f'<text x="30" y="34" class="mono" font-size="11" fill="{c["faint"]}">VAKAO / CONTRIBUTION STREAK</text>'
    vals = [("CURRENT", f"{current} d"), ("LONGEST", f"{longest} d"), ("TOTAL", f"{total:,}")]
    for i, (label, val) in enumerate(vals):
        x = 30 + i*270
        s += f'<text x="{x}" y="112" font-size="48" font-weight="700" fill="{c["ink"]}">{val}</text>'
        s += f'<text x="{x}" y="144" class="mono" font-size="10" fill="{c["muted"]}">{label}</text>'
    s += f'<rect x="30" y="180" width="{w-60}" height="3" fill="#F0995F" opacity=".75"/>'
    s += footer(c, w, h, "STREAK") + '</svg>'
    return s

def activity_card(days, dark=False):
    c = LIGHT if not dark else DARK
    w, h = 1000, 280
    c, s = card(w, h, dark)
    s += f'<text x="30" y="34" class="mono" font-size="11" fill="{c["faint"]}">VAKAO / ACTIVITY · LAST 52 WEEKS</text>'
    # days: ISO date string -> count
    today = date.today()
    start = today - timedelta(days=363)
    weeks = []
    for i in range(52):
        ws = start + timedelta(days=i*7)
        weeks.append(sum(days.get((ws + timedelta(days=j)).isoformat(), 0) for j in range(7)))
    mx = max(weeks) or 1
    x0, y0, bw, bh = 30, 78, 940, 150
    s += f'<line x1="{x0}" y1="{y0+bh}" x2="{x0+bw}" y2="{y0+bh}" stroke="{c["line"]}"/>'
    for i, v in enumerate(weeks):
        bh2 = max(2, v/mx*bh)
        s += f'<rect x="{x0+i*(bw/52):.1f}" y="{y0+bh-bh2:.1f}" width="{max(3,bw/52-4):.1f}" height="{bh2:.1f}" rx="2" fill="{COLORS[0] if v else c["line"]}" opacity="{0.85 if v else 0.5}"/>'
    s += f'<text x="{w-30}" y="34" text-anchor="end" class="mono" font-size="11" fill="{c["faint"]}">52 WEEKS · PEAK {mx}</text>'
    s += footer(c, w, h, "ACTIVITY") + '</svg>'
    return s

def project_card(name, desc, stars, lang, dark=False):
    c = LIGHT if not dark else DARK
    w, h = 600, 220
    c, s = card(w, h, dark)
    s += f'<text x="24" y="30" class="mono" font-size="10" fill="{c["faint"]}">VAKAO / PROJECT</text>'
    s += f'<text x="24" y="64" font-size="22" font-weight="700" fill="{c["ink"]}">{escape(name)}</text>'
    # wrap desc manually
    words = desc.split(); lines=[]; cur=''
    for word in words:
        if len(cur+word) > 36:
            lines.append(cur.strip()); cur=word
        else: cur += word + ' '
    if cur: lines.append(cur.strip())
    for i,line in enumerate(lines[:3]):
        s += f'<text x="24" y="{94+i*20}" font-size="13" fill="{c["muted"]}">{escape(line)}</text>'
    s += f'<text x="24" y="190" font-size="12" fill="{c["faint"]}">★ {stars}  ·  {escape(lang or "—")}</text>'
    s += f'<rect x="{w-52}" y="48" width="26" height="26" rx="7" fill="{c["accent"]}" opacity=".9"/>'
    s += f'<text x="{w-39}" y="66" text-anchor="middle" font-size="16" fill="white">★</text>'
    s += '</svg>'
    return s

def main():
    user = req(f"{API}/users/{LOGIN}")
    repos = req(f"{API}/users/{LOGIN}/repos?per_page=100&type=owner&sort=updated")
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
    langs = {}
    for r in repos:
        try:
            for k, v in req(r["languages_url"]).items():
                langs[k] = langs.get(k, 0) + int(v)
        except Exception:
            pass
    langs = dict(sorted(langs.items(), key=lambda kv: kv[1], reverse=True))
    days = {}
    total = 0
    try:
        g = req(f"{API}/graphql", {"query": 'query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}', "variables": {"login": LOGIN}})
        cal = g["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        total = cal["totalContributions"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    except Exception as e:
        print("contribution query failed:", e)
    if not days:
        raise SystemExit("contribution data is empty; refusing to write blank activity cards")
    # streak
    ordered = sorted(days)
    longest = cur = 0
    prev = None
    for d in ordered:
        v = days[d]
        if v > 0:
            cur = cur + 1 if prev == (date.fromisoformat(d) - timedelta(days=1)).isoformat() else 1
        else:
            cur = 0
        longest = max(longest, cur); prev = d
    # current streak ending today/yesterday
    current = 0; d = date.today()
    if days.get(d.isoformat(), 0) == 0:
        d -= timedelta(days=1)
    while days.get(d.isoformat(), 0) > 0:
        current += 1; d -= timedelta(days=1)
    for dark, suffix in [(False, ""), (True, "-dark")]:
        save(f"stats{suffix}.svg", stats_card(user, repos, stars, total, dark))
        save(f"languages{suffix}.svg", languages_card(langs, dark))
        save(f"streak{suffix}.svg", streak_card(current, longest, total, dark))
        save(f"activity{suffix}.svg", activity_card(days, dark))
    projects = [
        ("Vakao-Studio", "VaKao 团队官网：Nuxt 4 + Tailwind CSS + Three.js，静态生成。"),
        ("WireDeck", "在电脑上无线管理安卓手机：配对、应用、文件、日志与 Shell。"),
        ("DianMo", "点墨：Android 内存扫描与修改工具，Kotlin + C++ native。"),
        ("OnmyojiTools", "阴阳师 Windows 工具：多开、窗口排列、声音聚焦。"),
        ("VakaoUI", "Vue 3 + TypeScript 的现代化组件库。"),
        ("VakaoStaticHub", "静态资源管理：多根目录、分片上传、分享与更新中心。"),
    ]
    by_name = {r["name"]: r for r in repos}
    for name, desc in projects:
        r = by_name.get(name, {})
        for dark, suffix in [(False, ""), (True, "-dark")]:
            (PROJECTS / f"{name}{suffix}.svg").write_text(project_card(name, desc, r.get("stargazers_count", 0), r.get("language") or "", dark), encoding="utf-8")
    print(f"cards generated: {len(list(OUT.glob('*.svg')))} generated, {len(list(PROJECTS.glob('*.svg')))} project")

if __name__ == "__main__":
    main()
