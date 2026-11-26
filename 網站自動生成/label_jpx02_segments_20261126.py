#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JPX-02 曲目頁使用作品「段落標記」（孝瓏 2026-11-26 20:52）
  angels-wish: YOYO點點名專輯1 - 親子搖擺童樂會 → （夜裡沒有小黑鬼）
  exciting-adventure-team: 巧連智快樂版 2009年02月號 DVD → （培養專注力 一起來聽CD）
幂等：已有標記就跳過。用法： --apply
"""
import os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL2 = os.path.join(BASE, '罐頭音樂研究所', '圖書館音樂', 'dl-music', 'jpx-pro-vol2')
APPLY = '--apply' in sys.argv

JOBS = [
    ('angels-wish-yamato-yuko',
     '罐頭音樂研究所/yoyotv/yoyo點點名/yoyo點點名專輯/yoyo點點名專輯1-親子搖擺童樂會',
     '夜裡沒有小黑鬼'),
    ('exciting-adventure-team-yamato-yuko',
     '罐頭音樂研究所/巧連智/快樂版/巧連智快樂版dvd/巧連智快樂版2009年02月號dvd',
     '培養專注力 一起來聽CD'),
]

for slug, target, label in JOBS:
    p = os.path.join(VOL2, slug, 'index.html')
    h = open(p, encoding='utf-8').read()
    enc = urllib.parse.quote(target)
    pat = re.compile(r'<li><a href="/music-library/' + re.escape(enc) +
                     r'/"[^>]*>[^<]*</a>(<span class="lbl">（[^<]*）</span>)?</li>')
    m = pat.search(h)
    if not m:
        print('找不到列:', slug, target)
        continue
    if m.group(1):
        print('已有標記，跳過:', slug, m.group(1))
        continue
    name = re.search(r'>([^<]*)</a>', m.group(0)).group(1)
    new_li = ('<li><a href="/music-library/%s/">%s</a>'
              '<span class="lbl">（%s）</span></li>' % (enc, name, label))
    h2 = h[:m.start()] + new_li + h[m.end():]
    if APPLY:
        open(p, 'w', encoding='utf-8').write(h2)
    print(('已標記: ' if APPLY else '[DRY] ') + slug + ' → ' + name + '（' + label + '）')
print('APPLY' if APPLY else 'DRY-RUN')
