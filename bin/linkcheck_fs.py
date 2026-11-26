#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站連結健檢（可排程用）：URL 解碼後逐頁檢查站內連結是否存在。
2026-11-26：linkcheck_site.py 的 broken_total 與實際不符（它只處理部分相對連結、
且對 5 層深頁面的 ../ 層數判斷有誤），改用本支以檔案系統實測。
用法：python3 bin/linkcheck_fs.py [--verbose] [目錄]   （預設掃全站）
輸出：最後一行 JSON {pages, broken_unique, broken_total}
"""
import os, re, sys, json, glob, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
ROOT = os.path.join(BASE, ARGS[0]) if ARGS else BASE
VERBOSE = '--verbose' in sys.argv
SKIP_DIRS = {'bin', '網站自動生成', 'assets', '.git', 'node_modules'}

def check(href, page_dir, page_path):
    if not href or href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#', 'javascript:', 'data:')):
        return None
    href = href.split('#')[0].split('?')[0]
    if not href:
        return None
    h = urllib.parse.unquote(href)
    if h.startswith('/music-library/'):
        t = os.path.join(BASE, h[len('/music-library/'):])
    elif h.startswith('/'):
        return None  # 站台根目錄外的絕對路徑，另計
    else:
        t = os.path.normpath(os.path.join(page_dir, h))
    if t.endswith('/'):
        t = os.path.join(t, 'index.html')
    elif not os.path.splitext(t)[1]:
        t = os.path.join(t, 'index.html')
    if os.path.isfile(t):
        return None
    return (href, page_path)

def main():
    pages = 0
    broken_total = 0
    uniq = {}
    for p in glob.glob(os.path.join(ROOT, '**', 'index.html'), recursive=True):
        rel = os.path.relpath(p, BASE)
        if any(part in SKIP_DIRS for part in rel.split(os.sep)):
            continue
        pages += 1
        s = open(p, encoding='utf-8', errors='ignore').read()
        d = os.path.dirname(p)
        for href in set(re.findall(r'(?:href|src)="([^"]+)"', s)):
            r = check(href, d, rel)
            if r:
                broken_total += 1
                uniq[r[0]] = uniq.get(r[0], 0) + 1
    out = {'pages': pages, 'broken_unique': len(uniq), 'broken_total': broken_total}
    if VERBOSE:
        for k, v in sorted(uniq.items(), key=lambda x: -x[1])[:20]:
            print(v, k)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == '__main__':
    main()
