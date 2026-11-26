#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""左欄子清單＝照主內容卡片排法（2026-11-26 孝瓏定案：「照卡片排法，也就是中間的排法」）

規則：
1. 找到左欄「本頁節點」的就地展開子清單 <ul class="tree sub">（或節目頁的 <div class="tree-h">節目名</div><ul class="tree">）
2. 以主內容卡片順序（a.row / a.album-card）為唯一標準重排
3. 任何一項對不上卡片 → 該頁跳過（不冒險）
4. 只改順序，不動名稱、不動 href、不動其他節點

用法：
  python3 fix_tree_order_card_20261126.py --dry-run
  python3 fix_tree_order_card_20261126.py
"""
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv

SUB_RE = re.compile(r'(<ul class="tree sub">)(.*?)(</ul>)', re.S)
SEC_RE = re.compile(r'(<div class="tree-h">)([^<]{1,60})(</div>\s*<ul class="tree">)(.*?)(</ul>)', re.S)
LI_RE = re.compile(r'<li[^>]*>.*?</li>', re.S)
CARD_RE = re.compile(r'<a class="(?:row|album-card)"[^>]*href="([^"]+)"')


def norm(href):
    u = urllib.parse.unquote(href).rstrip('/')
    segs = [s for s in u.split('/') if s not in ('', '.', '..')]
    if 'music-library' in segs:
        segs = segs[segs.index('music-library') + 1:]
    return '/'.join(segs)


def sort_items(items, card_keys):
    pos = []
    for li in items:
        mm = re.search(r'href="([^"]+)"', li)
        if not mm:
            return None
        k = norm(mm.group(1))
        found = None
        for i, ck in enumerate(card_keys):
            if ck == k or ck.endswith('/' + k) or k.endswith('/' + ck):
                found = i
                break
        if found is None:
            return None
        pos.append(found)
    if pos == sorted(pos):
        return items  # 已一致
    return [items[i] for i in sorted(range(len(items)), key=lambda i: pos[i])]


changed = files = 0
detail = []
skipped = 0

for dirpath, _, fs in os.walk(ROOT):
    if 'index.html' not in fs:
        continue
    path = os.path.join(dirpath, 'index.html')
    h = open(path, encoding='utf-8').read()
    card_keys = [norm(c) for c in CARD_RE.findall(h)]
    if len(card_keys) < 2:
        continue
    rel = os.path.relpath(path, BASE)
    new = h
    touched = False

    # (A) 就地展開子清單（含本頁節點本身那一項 → 重排時把「本頁節點」固定在原位）
    for m in reversed(list(SUB_RE.finditer(h))):
        items = LI_RE.findall(m.group(2))
        if len(items) < 3:
            continue
        head = None
        body = items
        # 第 1 項若是「本頁節點」（後面還帶子清單），保持它在最前面
        if 'tree sub' in items[0]:
            head, body = items[0], items[1:]
        ordered = sort_items(body, card_keys)
        if ordered is None:
            skipped += 1
            continue
        if ordered == body:
            continue
        allitems = ([head] if head else []) + ordered
        new = new[:m.start()] + m.group(1) + ''.join(allitems) + m.group(3) + new[m.end():]
        touched = True
        detail.append((rel, len(ordered)))
        break

    # (B) 節目頁：<div class="tree-h">節目名</div><ul class="tree">
    if not touched:
        prog = os.path.basename(dirpath)
        for m in reversed(list(SEC_RE.finditer(h))):
            title = m.group(2).strip()
            if title.lower() != prog.lower():
                continue
            items = LI_RE.findall(m.group(4))
            if len(items) < 2:
                continue
            ordered = sort_items(items, card_keys)
            if ordered is None:
                skipped += 1
                continue
            if ordered == items:
                continue
            new = new[:m.start()] + m.group(1) + m.group(2) + m.group(3) + ''.join(ordered) + m.group(5) + new[m.end():]
            touched = True
            detail.append((rel, len(ordered)))
            break

    if touched and new != h:
        files += 1
        changed += 1
        if not DRY:
            open(path, 'w', encoding='utf-8').write(new)

print(f'{"[DRY] " if DRY else ""}重排 {changed} 頁（跳過對不上 {skipped} 個區塊）')
for rel, n in detail[:30]:
    print(f'  {rel[:80]}  ({n} 項)')
