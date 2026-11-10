#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修站內 404：麵包屑壞連結、舊品牌名、相對連結（狗狗週記）"""
import os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r'href="([^"]+)"')

def resolve(pdir, url):
    u = url.split("#")[0].split("?")[0]
    if not u:
        return None
    u = urllib.parse.unquote(u)
    if u.startswith("/music-library/"):
        p = os.path.join(BASE, u[len("/music-library/"):])
    elif u.startswith("/"):
        p = os.path.join(BASE, u.lstrip("/"))
    else:
        p = os.path.normpath(os.path.join(pdir, u))
    if p.endswith("/"):
        p += "index.html"
    if os.path.isdir(p):
        p = os.path.join(p, "index.html")
    return p

def norm(s):
    s = urllib.parse.unquote(s).lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)
    return s

fixed_crumb = fixed_rel = fixed_brand = 0

for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "assets"}]
    if "index.html" not in files:
        continue
    p = os.path.join(root, "index.html")
    s = open(p, encoding="utf-8", errors="ignore").read()
    orig = s
    rel = os.path.relpath(root, BASE)
    depth = 0 if rel == "." else len(rel.split(os.sep))
    ancestors = [] if rel == "." else rel.split(os.sep)
    abs_prefix = "/music-library/" + urllib.parse.quote("/".join(ancestors) + "/") if ancestors else "/music-library/"

    # 1) 舊品牌名 Deep East Music → deep-east
    if "Deep%20East%20Music" in s:
        s = s.replace("Deep%20East%20Music", "deep-east")
        fixed_brand += 1

    # 2) 狗狗週記 相對連結 → 絕對
    if rel.startswith("罐頭音樂研究所/海綿寶寶"):
        def fixdg(m):
            global fixed_rel
            url = m.group(1)
            if url.startswith(("http", "/", "#", "..")):
                return m.group(0)
            if not url.startswith("%E7%8B%97"):   # 狗狗週記-
                return m.group(0)
            fixed_rel += 1
            return 'href="/music-library/%s"' % urllib.parse.quote(
                "罐頭音樂研究所/momo親子台/狗狗週記/" + urllib.parse.unquote(url))
        s = LINK.sub(fixdg, s)

    # 3) 麵包屑壞連結
    m = re.search(r'(<div class="crumb">)(.*?)(</div>)', s, re.S)
    if m:
        body = m.group(2)
        def fixcrumb(mm):
            global fixed_crumb
            url = mm.group(1)
            if url.startswith(("http", "/", "mailto:", "#")):
                return mm.group(0)
            if resolve(root, url) and os.path.exists(resolve(root, url)):
                return mm.group(0)
            # 用標籤比對祖先資料夾
            label = mm.group(2)
            best = None
            for i, a in enumerate(ancestors):
                if norm(a) and norm(a) in norm(label):
                    best = i
            if best is not None:
                path = "/".join(ancestors[: best + 1]) + "/"
                fixed_crumb += 1
                return 'href="/music-library/%s"' % urllib.parse.quote(path)
            # 退回：裁到最近存在層
            for k in range(len(ancestors), -1, -1):
                path = "/".join(ancestors[:k]) + ("/" if k else "")
                cand = os.path.join(BASE, path, "index.html")
                if os.path.exists(cand):
                    fixed_crumb += 1
                    return 'href="/music-library/%s"' % urllib.parse.quote(path)
            return mm.group(0)
        nb = re.sub(r'href="([^"]*)"(?:[^>]*)>([^<]*)</a>', fixcrumb, body)
        if nb != body:
            s = s[:m.start(2)] + nb + s[m.end(2):]

    if s != orig:
        open(p, "w", encoding="utf-8").write(s)

print({"crumb": fixed_crumb, "rel": fixed_rel, "brand": fixed_brand})
