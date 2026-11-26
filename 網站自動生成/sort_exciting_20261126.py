#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ワクワク冒険隊 曲目頁「使用作品」排序（孝瓏 2026-11-26 20:38）
網站品牌順序：公視 > YOYOTV > MOMO > 巧連智 > 古古食
→ YOYO點點名 第04季 第028集（YOYOTV）在上
→ 巧連智快樂版 2009年02月號 DVD（巧連智）在下
用法： python3 sort_exciting_20261126.py [--dry]
"""
import os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所', '圖書館音樂', 'dl-music', 'jpx-pro-vol2',
                    'exciting-adventure-team-yamato-yuko', 'index.html')
ORDER = ['yoyotv', '巧連智']  # 品牌優先序（由網站選單）
DRY = '--dry' in sys.argv


def brand_rank(href):
    u = urllib.parse.unquote(href)
    for i, b in enumerate(ORDER):
        if '/罐頭音樂研究所/%s/' % b in u:
            return i
    return 99


s = open(PAGE, encoding='utf-8').read()
m = re.search(r'(<ul class="entries">)(.*?)(</ul>)', s, re.S)
# 第一段是 YouTube 播放框，取最後一個有作品連結的 ul
matches = list(re.finditer(r'(<ul class="entries">)(.*?)(</ul>)', s, re.S))
tgt = None
for mm in matches:
    if re.search(r'<a href="/music-library/', mm.group(2)):
        tgt = mm
assert tgt, '找不到使用作品區'
items = re.findall(r'<li[^>]*>.*?</li>', tgt.group(2), re.S)
new = sorted(items, key=lambda it: brand_rank(re.search(r'<a href="([^"]+)"', it).group(1)))
if [re.search(r'<a href="([^"]+)"', x).group(1) for x in items] == \
   [re.search(r'<a href="([^"]+)"', x).group(1) for x in new]:
    print('已正確排序，無變更')
    sys.exit(0)
sep = '\n'
out = s[:tgt.start(2)] + sep.join(new) + s[tgt.end(2):]
if not DRY:
    open(PAGE, 'w', encoding='utf-8').write(out)
for x in new:
    print('  ', urllib.parse.unquote(re.search(r'<a href="([^"]+)"', x).group(1))[-50:])
print('[DRY]' if DRY else 'APPLIED')
