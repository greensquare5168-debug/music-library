#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正麵包屑相對層數（depth-5 頁誤用 4 層 ../ 造成 404）"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRUMB = re.compile(r'(<div class="crumb">)(.*?)(</div>)', re.S)
HREF = re.compile(r'href="((?:\.\./)+)([^"]*)"')

changed = 0
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "assets"}]
    if "index.html" not in files:
        continue
    rel = os.path.relpath(root, BASE)
    depth = 0 if rel == "." else len(rel.split(os.sep))
    p = os.path.join(root, "index.html")
    s = open(p, encoding="utf-8", errors="ignore").read()
    m = CRUMB.search(s)
    if not m:
        continue
    body = m.group(2)
    def fix(mm):
        want = "../" * depth
        return 'href="%s%s"' % (want, mm.group(2))
    nb = HREF.sub(fix, body)
    if nb != body:
        s = s[:m.start(2)] + nb + s[m.end(2):]
        open(p, "w", encoding="utf-8").write(s)
        changed += 1
print("crumb fixed pages:", changed)
