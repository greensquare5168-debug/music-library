#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""作品頁（集頁）JPX 曲目外部連結改指向 YouTube（孝瓏 2026-11-26 20:57）
規則：曲目頁有 YouTube 影片 → 作品頁該曲目的外部連結改用 https://www.youtube.com/watch?v=<id>
      並保留 <span class="lbl">（專輯）</span> 與 ↗ 本站曲目頁連結不變。
範圍：所有含 JPX 官方連結（dl.music-yamato.jp）的作品頁；本次只換 JPX-02 三首
      （ピエロの帽子 / Fairytale / 天使の願いごと → 另有 excitedAdventure 對應）
用法： python3 jpx02_works_to_yt_20261126.py [--apply]
"""
import os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL2 = os.path.join(BASE, '罐頭音樂研究所', '圖書館音樂', 'dl-music', 'jpx-pro-vol2')
APPLY = '--apply' in sys.argv

# slug → YouTube 影片 id（取自各曲目頁 ytframe）
YT = {}
for slug in ['clown-hat', 'thumb-princess', 'angels-wish', 'exciting-adventure-team',
             'clown-balloon', 'a-pegasus']:
    p = os.path.join(VOL2, slug + '-yamato-yuko', 'index.html')
    s = open(p, encoding='utf-8').read()
    m = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', s)
    YT[slug] = m.group(1) if m else None

# 官方連結 → (slug) 對照（舊/新檔名都吃）
OFFICIAL = {
    'https://dl.music-yamato.jp/JPX-vol02_1.html': 'clown-hat',
    'https://dl.music-yamato.jp/JPX-vol02_2.html': 'thumb-princess',
    'https://dl.music-yamato.jp/JPX-vol02_3.html': 'angels-wish',
}
print('YT ids:', YT)

LI_RE = re.compile(r'<li><a href="(https://dl\.music-yamato\.jp/[^"]+)"([^>]*)>([^<]*)</a>(.*?)</li>', re.S)
changed_files, changed_rows, skipped = 0, 0, 0

for dp, dns, fs in os.walk(os.path.join(BASE, '罐頭音樂研究所')):
    dns[:] = [d for d in dns if d != 'dl-music']
    if 'index.html' not in fs:
        continue
    p = os.path.join(dp, 'index.html')
    s = open(p, encoding='utf-8').read()
    if 'dl.music-yamato.jp' not in s:
        continue
    new = s
    # 有 JPX 曲目但整頁沒有 YouTube → 該曲目改用官方新連結（站方改檔名）
    if 'youtube.com/watch' not in s:
        for url, slug in OFFICIAL.items():
            if url in s and YT.get(slug):
                continue
    for old in ('JPX-02_1', 'JPX-02_2', 'JPX-02_3'):
        new = new.replace('https://dl.music-yamato.jp/%s.html' % old,
                          'https://dl.music-yamato.jp/JPX-vol02_%s.html' % old[-1])
    s = new if new != s else s
    for m in list(LI_RE.finditer(s)):
        url, attrs, name, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        slug = OFFICIAL.get(url)
        if not slug or not YT.get(slug):
            skipped += 1
            continue
        yt = 'https://www.youtube.com/watch?v=%s' % YT[slug]
        li = '<li><a href="%s"%s>%s</a>%s</li>' % (yt, attrs, name, rest)
        new = new.replace(m.group(0), li, 1)
        changed_rows += 1
    if new != s:
        changed_files += 1
        if APPLY:
            open(p, 'w', encoding='utf-8').write(new)

print('改頁數:', changed_files, '| 改列數:', changed_rows, '| 未對應(保留):', skipped)
print('APPLY' if APPLY else 'DRY-RUN')
