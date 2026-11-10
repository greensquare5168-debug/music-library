#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站內連結健檢：找出 404（目標檔案不存在）的內部連結
用法：python3 bin/linkcheck_site.py [--fix] [--scope 路徑前綴]
"""
import os, re, sys, json, urllib.parse, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "node_modules", "assets"}
LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')

def target_ok(page_dir, url):
    if url.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
        return True
    u = url.split("#")[0].split("?")[0]
    if not u:
        return True
    u = urllib.parse.unquote(u)
    if u.startswith("/music-library/"):
        p = os.path.join(BASE, u[len("/music-library/"):])
    elif u.startswith("/"):
        p = os.path.join(BASE, u.lstrip("/"))
    else:
        p = os.path.normpath(os.path.join(page_dir, u))
    if p.endswith("/"):
        p += "index.html"
    if os.path.isdir(p):
        p = os.path.join(p, "index.html")
    return os.path.exists(p)

def main():
    fix = "--fix" in sys.argv
    scope = None
    if "--scope" in sys.argv:
        scope = sys.argv[sys.argv.index("--scope") + 1]
    missing = collections.Counter()
    pages = 0
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = os.path.relpath(root, BASE)
        if scope and not rel_root.startswith(scope):
            continue
        if "index.html" not in files:
            continue
        pages += 1
        p = os.path.join(root, "index.html")
        try:
            s = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for url in set(LINK_RE.findall(s)):
            if not target_ok(root, url):
                missing[url] += 1
    print(json.dumps({"pages": pages, "broken_unique": len(missing),
                      "broken_total": sum(missing.values())}, ensure_ascii=False))
    for u, c in missing.most_common(40):
        print(c, u)

if __name__ == "__main__":
    main()
