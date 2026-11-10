#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SCD-262 曲名去尾碼 A：改 h1/title/麵包屑/目錄/專輯列/左欄/tree-lib/search-index"""
import json, os, re, subprocess, urllib.parse, unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SON = "罐頭音樂研究所/圖書館音樂/sonoton"
ADIR = "scd262-lounge-exotica"
FULL = os.path.join(BASE, SON, ADIR)

def slug(s):
    s = unicodedata.normalize("NFKD", s).replace("&", " and ")
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[^0-9A-Za-z]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()

def read(p): return open(os.path.join(BASE, p), encoding="utf-8").read()
def write(p, s): open(os.path.join(BASE, p), "w", encoding="utf-8").write(s)

plan = []
for d in sorted(os.listdir(FULL)):
    p = os.path.join(FULL, d, "index.html")
    if not os.path.isfile(p):
        continue
    s = open(p, encoding="utf-8").read()
    m = re.search(r"<h1>(.*?) - (.*?)</h1>", s)
    title = m.group(1).replace("&amp;", "&")
    comp = m.group(2).replace("&amp;", "&")
    new_title = re.sub(r"\s+[AB]$", "", title).strip()
    if new_title == title:
        continue
    code = re.search(r"-scd(\d+)$", d).group(1)
    new_dir = "%s-%s" % (slug("%s %s" % (new_title, comp)), d[len(d) - len(d.split("-scd")[-1]) - 4:]) if False else None
    nd = "%s-scd%s" % (slug("%s %s" % (new_title, comp)), code)
    plan.append((d, nd, title, new_title, comp))

print("to fix", len(plan))
for d, nd, t, nt, c in plan:
    print("  %-45s -> %-45s (%s -> %s)" % (d, nd, t, nt))

# 1) 目錄改名
for d, nd, *_ in plan:
    src = os.path.join(FULL, d)
    dst = os.path.join(FULL, nd)
    if os.path.exists(dst):
        print("SKIP exists", nd)
        continue
    subprocess.run(["git", "mv", src, dst], check=False)

# 2) 頁面內文字
for d, nd, t, nt, c in plan:
    p = SON + "/" + ADIR + "/" + nd + "/index.html"
    s = read(p)
    s = s.replace("<h1>%s - %s</h1>" % (t.replace("&", "&amp;"), c.replace("&", "&amp;")),
                  "<h1>%s - %s</h1>" % (nt.replace("&", "&amp;"), c.replace("&", "&amp;")))
    s = re.sub(r"<title>.*?</title>", "<title>%s - %s｜圖書館音樂研究所</title>" % (nt.replace("&", "&amp;"), c.replace("&", "&amp;")), s, count=1, flags=re.S)
    # 麵包屑最後一段
    s = s.replace("> %s - %s</div>" % (t.replace("&", "&amp;"), c.replace("&", "&amp;")),
                  "> %s - %s</div>" % (nt.replace("&", "&amp;"), c.replace("&", "&amp;")))
    write(p, s)

# 3) 全域把舊 slug 換新 slug + 標題字串
repls = [(d, nd) for d, nd, *_ in plan] + [(t, nt) for d, nd, t, nt, c in plan if t.endswith((" A", " B"))]
for root, dirs, files in os.walk(BASE):
    dirs[:] = [x for x in dirs if x not in {".git", "assets", "node_modules", "bin"}]
    for f in files:
        if not (f.endswith(".html") or f in ("search-index.json", "tree-lib.json")):
            continue
        p = os.path.join(root, f)
        s = open(p, encoding="utf-8", errors="ignore").read()
        o = s
        for a, b in repls:
            s = s.replace(a, b)
        if s != o:
            open(p, "w", encoding="utf-8").write(s)

# 4) 專輯列重建
YT = ('<span class="srcb" style="position:relative;display:inline-flex;align-items:center;justify-content:center;'
      'width:43px;height:24px;flex:0 0 43px;margin-left:6px;margin-right:10px">'
      '<span class="ytbadge ytimg" title="YouTube" style="position:static;margin:0;padding:0;background:none;'
      'border-radius:0;box-shadow:none;min-width:0;display:flex;align-items:center;justify-content:center;line-height:0">'
      '<img src="../../../../assets/yt-logo.png" alt="YouTube" title="YouTube" style="display:block;max-width:26px;max-height:22px;width:auto;height:auto">'
      '</span></span>')
MY = ('<span class="mark" title="有發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;'
      'width:18px;height:18px;padding:0;line-height:1;font-size:11px;background:#eaf7ef;color:#12894a;'
      'border:1px solid #bfe6cd">✓</span>')
MX = ('<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;'
      'justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>')
GO = ('<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;'
      'line-height:1;transform:translateY(0.5px)">›</span>')

def codenum(d):
    m = re.search(r"-scd(\d+)$", d)
    return (int(m.group(1)[:6]), m.group(1)[6:]) if m else (999999, "")

dirs = sorted((d for d in os.listdir(FULL) if os.path.isdir(os.path.join(FULL, d))), key=codenum)
rows = []
for d in dirs:
    s = read(SON + "/" + ADIR + "/" + d + "/index.html")
    m = re.search(r"<h1>(.*?) - (.*?)</h1>", s)
    t, c = m.group(1), m.group(2)
    used = t in ("Death Trap", "Bossa Cubana")
    rows.append('<li><a class="row" href="/music-library/%s"><span class="rn">%s<span class="rnsub">%s</span></span>'
                '<span class="muted"></span>%s%s%s</a></li>' % (
                    urllib.parse.quote(SON + "/" + ADIR + "/" + d + "/"), t, c, MY if used else MX, YT, GO))
alb = SON + "/" + ADIR + "/index.html"
s = read(alb)
m = re.search(r'(<ul class="albumlist">)(.*?)(</ul>)', s, re.S)
s = s[:m.start(2)] + "".join(rows) + s[m.end(2):]
write(alb, s)
print("album rows", len(rows))
