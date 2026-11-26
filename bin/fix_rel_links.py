#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修全站相對連結（2026-11-26，取代半調子的 fix_rel_links.py）
規則：所有「以 ../ 開頭」的相對連結，一律依頁面實際位置解析成站台絕對路徑
      /music-library/<repo 相對路徑>（含 ?query / #hash）
      若解析出的目標不存在（父層數多算），會往少算一層再試，最多差 3 層。
      目標不存在且無法修正 → 保留原樣並列入報告。
用法：--apply
"""
import os, re, sys, glob, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv
URLATTR = re.compile(r'((?:href|src)=")([^"]+)(")')

stats = {'fixed': 0, 'unresolvable': 0}
unres = set()

def exists(relpath):
    relpath = relpath.split('?')[0].split('#')[0]
    t = os.path.join(BASE, relpath)
    if t.endswith('/') or not os.path.splitext(t)[1]:
        t = os.path.join(t, 'index.html')
    return os.path.isfile(t)

for p in glob.glob(os.path.join(BASE, '**', 'index.html'), recursive=True):
    rel = os.path.relpath(p, BASE)
    if rel.split(os.sep)[0] in ('bin', '網站自動生成', '.git'):
        continue
    s = open(p, encoding='utf-8', errors='ignore').read()
    page_dir = os.path.dirname(p)
    changed = [False]

    def sub(m):
        href = m.group(2)
        if not href.startswith('../'):
            return m.group(0)
        core = href.split('?')[0].split('#')[0]
        tail = href[len(core):]
        h = urllib.parse.unquote(core)
        cands = []
        for delta in (0, -1, -2, -3, 1):
            up = h.count('../') + delta
            rest = h
            while rest.startswith('../'):
                rest = rest[3:]
            if up < 0:
                continue
            d = page_dir
            for _ in range(up):
                d = os.path.dirname(d)
            cands.append(os.path.normpath(os.path.join(d, rest)))
        for c in cands:
            if exists(os.path.relpath(c, BASE)):
                newrel = os.path.relpath(c, BASE)
                if newrel == os.path.relpath(os.path.normpath(os.path.join(page_dir, h)), BASE):
                    return m.group(0)  # 本來就對
                changed[0] = True
                stats['fixed'] += 1
                return m.group(1) + '/music-library/' + urllib.parse.quote(newrel).replace('%2F', '/') + tail + m.group(3)
        stats['unresolvable'] += 1
        unres.add((href, rel))
        return m.group(0)

    s2 = URLATTR.sub(sub, s)
    if changed[0] and APPLY:
        open(p, 'w', encoding='utf-8').write(s2)

print(stats)
for u in list(unres)[:15]:
    print('無法解析:', u)
print('APPLY' if APPLY else 'DRY-RUN')
