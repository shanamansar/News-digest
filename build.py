#!/usr/bin/env python3
"""Reads iranintl.com (Persian) and writes docs/index.html: a dark, RTL, bullet-style digest.
Run it on a schedule (see .github/workflows/update.yml). Needs only the Python standard library."""
import html, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.iranintl.com"
PER_SECTION = 8
PAGES = {  # page path -> default section
    "/iran": "pol", "/finance": "eco", "/world": "world", "/sport": "sport",
}
SECTIONS = [("war", "جنگ ایران و آمریکا"), ("pol", "سیاست ایران"),
            ("eco", "اقتصاد ایران"), ("world", "سیاست جهان"), ("sport", "ورزش")]
# Keyword rules used to pick the section for stories from /iran and /world
WAR = ["آمریکا", "ترامپ", "سنتکام", "تنگه هرمز", "محاصره", "نتانیاهو", "اسرائیل", "حمله نظامی", "بمب‌افکن", "پنتاگون"]
ECO = ["تورم", "قیمت", "دلار", "ارز", "یارانه", "کالابرگ", "بورس", "اقتصاد", "کارگر", "حقوق", "بازنشست", "مرغ", "بانک", "نفت", "صادرات"]

ANCHOR = re.compile(r'<a\b[^>]*href="(?:https://www\.iranintl\.com)?/?((?:fa/)?\d{11,13})"[^>]*>(.*?)</a>', re.S)
HEAD = re.compile(r"<h\d[^>]*>(.*?)</h\d>", re.S)
TAGS = re.compile(r"<[^>]+>")

def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0 (news-digest bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(TAGS.sub(" ", s))).strip()

def stories(page_html):
    seen, out = set(), []
    for m in ANCHOR.finditer(page_html):
        sid, inner = m.group(1).replace("fa/", ""), m.group(2)
        h = HEAD.search(inner)
        title = clean(h.group(1) if h else inner)
        if sid in seen or len(title) < 15 or len(title) > 180:
            continue
        seen.add(sid)
        out.append((title, f"{BASE}/{sid}"))
    return out

def classify(title, default):
    if default in ("sport",):
        return default
    if any(k in title for k in WAR):
        return "war"
    if default == "pol" and any(k in title for k in ECO):
        return "eco"
    return default

def build():
    buckets = {k: [] for k, _ in SECTIONS}
    seen = set()
    for path, default in PAGES.items():
        try:
            items = stories(fetch(path))
        except Exception as e:
            print(f"warning: could not read {path}: {e}", file=sys.stderr)
            continue
        for title, url in items:
            if url in seen:
                continue
            seen.add(url)
            buckets[classify(title, default)].append((title, url))
    if not any(buckets.values()):
        sys.exit("No stories found; keeping the old page.")
    return buckets

def render(buckets):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    nav = "".join(f'<a href="#{k}">{html.escape(t)}</a>' for k, t in SECTIONS)
    secs = ""
    for k, t in SECTIONS:
        lis = "".join(f'<li><a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(x)}</a></li>'
                      for x, u in buckets[k][:PER_SECTION]) or '<li class="e">امروز خبر تازه‌ای در این بخش نیست.</li>'
        secs += f'<section id="{k}"><h2>{html.escape(t)}</h2><ul>{lis}</ul></section>'
    return TEMPLATE.replace("{{NAV}}", nav).replace("{{SECTIONS}}", secs).replace("{{NOW}}", now)

TEMPLATE = """<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>خلاصه اخبار ایران</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600&display=swap">
<style>
:root{--bg:#0b0d12;--card:#141821;--line:#232a38;--text:#e6e9f0;--mute:#8a93a6;--acc:#4da3ff;color-scheme:dark}
*{box-sizing:border-box}html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.9 Vazirmatn,Tahoma,system-ui,sans-serif}
header,main,footer{max-width:760px;margin:0 auto;padding:0 18px}header{padding-top:28px}
h1{margin:0 0 4px;font-size:26px}.sub{color:var(--mute);font-size:14px}
nav{position:sticky;top:0;background:var(--bg);z-index:5;display:flex;gap:8px;overflow-x:auto;padding:10px 18px;border-bottom:1px solid var(--line);max-width:760px;margin:0 auto}
nav a{white-space:nowrap;color:var(--text);text-decoration:none;font-size:14px;padding:2px 12px;border:1px solid var(--line);border-radius:99px;background:var(--card)}
section{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-top:16px}
h2{margin:0 0 8px;font-size:18px;color:var(--acc)}ul{margin:0;padding:0 20px 0 0}li{margin:8px 0}
li a{color:var(--text);text-decoration:none}li a:hover{color:var(--acc);text-decoration:underline}.e{color:var(--mute);list-style:none}
footer{padding:16px 18px 40px;color:var(--mute);font-size:13px}footer a{color:var(--acc)}
</style></head><body>
<header><h1>خلاصه اخبار ایران</h1>
<div class="sub">تیترهای ایران اینترنشنال · هر ساعت به‌روز می‌شود · آخرین به‌روزرسانی: {{NOW}}</div></header>
<nav>{{NAV}}</nav><main>{{SECTIONS}}</main>
<footer>منبع: <a href="https://www.iranintl.com/" target="_blank" rel="noopener">iranintl.com</a></footer>
<script>setTimeout(function(){location.reload()},3600000);</script>
</body></html>"""

if __name__ == "__main__":
    out = Path(__file__).parent / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render(build()), encoding="utf-8")
    print("wrote", out)
