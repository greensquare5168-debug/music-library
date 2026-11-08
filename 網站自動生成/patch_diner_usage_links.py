#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把巧連智使用頁裡「The Diner（din064）」曲目的連結，從 YouTube 換成 The Diner 官網曲目頁。
可重跑（已是 diner 連結就跳過）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://thedinermusic.com/tracks?tracks=din064-'

# 曲名 -> din064 編號（含 D-KD0017 Ethereal Vibes）
MAP = {
    'Ducks on a Train': 1,
    'Wacky Escapades': 3,
    'Music Box Slumbertime': 4,
    'Sixth Grade Rock': 5,
    'Go to Sleep': 7,
    'Making Sand Castles': 10,
    'Cartoony Vocal Dohs': 11,
    'Oompah Parade': 13,
    'Watch the Snow Fall': 15,
    "Doesn't That Feel Better": 18,
    'When the Elephant Saw the Mouse': 19,
    'Antics Abound': 20,
    'To Be Young Again': 21,
    'Playing in the Sun': 25,
    'March of the Puffins': 27,
    'Ethereal Vibes': 30,
}

changed = []
for f in list(Path(ROOT / '罐頭音樂研究所' / '巧連智').rglob('index.html')) + \
         list(Path(ROOT / '使用公司').rglob('index.html')):
    h = f.read_text(encoding='utf-8')
    orig = h
    for title, no in MAP.items():
        url = f'{BASE}{no}'
        pat = re.compile(r'<a href="(?!' + re.escape(url) + r')([^"]*thedinermusic\.com[^"]*|https?://(?!thedinermusic\.com)[^"]+)"([^>]*)>' + re.escape(title) + r'([^<]*)</a>')
        h = pat.sub(lambda m: f'<a href="{url}"{m.group(2)}>{title}{m.group(3)}</a>', h)
    if h != orig:
        f.write_text(h, encoding='utf-8')
        changed.append(f.parent.name)

print('patched pages:', len(changed))
for c in changed:
    print(' -', c)
