#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 tree-lib.json 重建「圖書館音樂」各頁的靜態左欄（修 404：層數錯、幽靈專輯、舊品牌名）"""
import json, os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = "罐頭音樂研究所/圖書館音樂"
tl = json.load(open(os.path.join(BASE, "tree-lib.json"), encoding="utf-8"))
root = tl[0]
BRANDS = root["c"]

def enc(p):
    return urllib.parse.quote(p)

ASIDE = re.compile(r'<aside class="treebox">.*?</aside>', re.S)

def render(seg_path, base):
    """seg_path: 目前頁面相對 圖書館音樂/ 的路徑片段 list"""
    items = []
    for b in BRANDS:
        bh = b["h"].rstrip("/")
        segs = bh.split("/")
        label = b["n"]
        inside_brand = seg_path[:1] == segs[:1]
        if not inside_brand:
            items.append('<li><a href="%s%s">%s</a></li>' % (base, enc(LIB + "/" + b["h"]), label))
            continue
        subs = []
        for a in b.get("c", []):
            ah = a["h"].rstrip("/")
            ase = ah.split("/")
            inside_album = seg_path[:2] == ase[:2]
            if not inside_album:
                subs.append('<li><a href="%s%s">%s</a></li>' % (base, enc(LIB + "/" + a["h"]), a["n"]))
                continue
            tsub = []
            for t in a.get("c", []):
                th = t["h"].rstrip("/")
                tse = th.split("/")
                cur = "cur" if seg_path[:3] == tse[:3] else ""
                tsub.append('<li%s><a href="%s%s">%s</a></li>' % (
                    ' class="cur"' if cur else "", base, enc(LIB + "/" + t["h"]), t["n"]))
            subs.append('<li class="cur open"><span class="arw">▾</span><a href="%s%s">%s</a><ul class="tree sub">%s</ul></li>'
                        % (base, enc(LIB + "/" + a["h"]), a["n"], "".join(tsub)))
        items.append('<li class="cur open"><span class="arw">▾</span><a href="%s%s">%s</a><ul class="tree sub">%s</ul></li>'
                     % (base, enc(LIB + "/" + b["h"]), label, "".join(subs)))
    return ('<aside class="treebox"><div class="tree-h"><a href="%s%s">音樂圖書館</a></div>'
            '<ul class="tree">%s</ul></aside>' % (base, enc(LIB + "/"), "".join(items)))

def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    changed = 0
    for r, dirs, files in os.walk(os.path.join(BASE, LIB)):
        dirs[:] = [d for d in dirs if d not in {"assets"}]
        if "index.html" not in files:
            continue
        rel = os.path.relpath(r, BASE)
        if only and not rel.startswith(only):
            continue
        depth = len(rel.split(os.sep))
        seg_path = rel.split(os.sep)[2:]
        base = "../" * depth
        p = os.path.join(r, "index.html")
        s = open(p, encoding="utf-8", errors="ignore").read()
        m = ASIDE.search(s)
        if not m:
            continue
        new = render(seg_path, base)
        if new != m.group(0):
            s = s[:m.start()] + new + s[m.end():]
            open(p, "w", encoding="utf-8").write(s)
            changed += 1
    print("aside rebuilt:", changed)

if __name__ == "__main__":
    main()
