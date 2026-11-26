#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曲目頁「使用作品」連結修復（2026-11-26 孝瓏：「作品點了404」）

症狀：曲目頁 <ul class="entries"> 裡的作品連結指向不存在的目錄 → 404。
      例：……/yoyotv/yoyo童話世界-第13集-鴨媽媽的寶貝蛋小小姑娘/（少了「yoyo童話世界/」這層）

修法：
 1. 先建立全站資料夾索引（相對 ROOT 的路徑，不含 index.html）
 2. 對每個 entries 連結，取目錄最後一段（slug）去索引找候選
 3. 只有「唯一候選」才修；多個候選或找不到 → 跳過並列報告
 4. 連結文字不動（名稱已正確），只改 href

用法： python3 fix_entries_links_20261126.py [--dry-run]
"""
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv

ENTRIES_RE = re.compile(r'(<ul class="entries">)(.*?)(</ul>)', re.S)
LI_RE = re.compile(r'<li[^>]*>.*?</li>', re.S)
A_RE = re.compile(r'<a href="([^"]+)"([^>]*)>')

# ---- 建立索引 ----
index = {}
for dirpath, dirs, fs in os.walk(ROOT):
    if 'index.html' not in fs:
        continue
    rel = os.path.relpath(dirpath, os.getcwd())
    slug = os.path.basename(dirpath)
    index.setdefault(slug, []).append(rel)

fixed = pages = 0
skipped = []

for dirpath, _, fs in os.walk(ROOT):
    if 'index.html' not in fs:
        continue
    path = os.path.join(dirpath, 'index.html')
    h = open(path, encoding='utf-8').read()
    page_rel = os.path.relpath(dirpath, os.getcwd())
    depth = len(page_rel.split(os.sep))

    new_h = h
    touched = 0

    for m in reversed(list(ENTRIES_RE.finditer(h))):
        body = m.group(2)
        new_body = body
        for li in reversed(LI_RE.findall(body)):
            am = A_RE.search(li)
            if not am:
                continue
            href = am.group(1)
            target = None
            if href.startswith('/music-library/'):
                target = urllib.parse.unquote(href[len('/music-library/'):]).rstrip('/')
                abs_target = os.path.join(os.getcwd(), target)
            else:
                target = os.path.normpath(os.path.join(page_rel, urllib.parse.unquote(href))).rstrip('/')
                abs_target = os.path.join(os.getcwd(), target)
            if os.path.isdir(abs_target):
                continue  # 正常

            slug = os.path.basename(target)
            cands = index.get(slug, [])
            if len(cands) != 1:
                skipped.append((page_rel, slug, len(cands)))
                continue
            good = cands[0]
            rel_from_page = os.path.relpath(good, page_rel)
            if not rel_from_page.startswith('.'):
                rel_from_page = './' + rel_from_page
            new_href = urllib.parse.quote(rel_from_page) + '/'
            # 保留原始 href 風格（絕對 vs 相對）：原為 /music-library/ 開頭就用絕對
            if href.startswith('/music-library/'):
                new_href = '/music-library/' + urllib.parse.quote(good) + '/'
            new_li = li.replace(f'<a href="{href}"', f'<a href="{new_href}"', 1)
            new_body = new_body.replace(li, new_li, 1)
            touched += 1
        if new_body != body:
            new_h = new_h[:m.start()] + m.group(1) + new_body + m.group(3) + new_h[m.end():]

    if new_h != h:
        pages += 1
        fixed += touched
        if not DRY:
            open(path, 'w', encoding='utf-8').write(new_h)

print(f'{"[DRY] " if DRY else ""}修 {fixed} 個連結，涉及 {pages} 頁')
if skipped:
    print(f'--- 未修 {len(skipped)} 個（多候選或找不到）')
    from collections import Counter
    c = Counter(s[1] for s in skipped)
    for slug, n in c.most_common(15):
        print(f'  {slug[:50]}  ×{n}')
