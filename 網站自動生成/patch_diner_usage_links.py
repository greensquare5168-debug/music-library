#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""巧連智使用頁：The Diner（din064）曲目 → 連結改成 Diner 官網、作者補成完整（& 依字母排序）。
可重跑（idempotent）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://thedinermusic.com/tracks?tracks=din064-'

# 曲名 -> (din064 編號, 完整作者字串；None = 不改作者)
MAP = {
    'Ducks on a Train': (1, 'Eric Kaye & Shenandi'),
    'Wacky Escapades': (3, 'Josh Peck & Shenandi'),
    'Music Box Slumbertime': (4, 'Scott Mann & Shenandi'),
    'Sixth Grade Rock': (5, 'Demian Sims'),
    'Go to Sleep': (7, 'Lisa Mazzotte'),
    'Making Sand Castles': (10, 'Jared Hunter'),
    'Cartoony Vocal Dohs': (11, 'Eric Kaye & Stephen Cullo'),
    'Oompah Parade': (13, 'Eric Kaye'),
    'Watch the Snow Fall': (15, 'Lisa Mazzotte'),
    "Doesn't That Feel Better": (18, 'Shenandi & Zack Hemsey'),
    'When the Elephant Saw the Mouse': (19, 'Jared Hunter'),
    'Antics Abound': (20, 'Nukorn Visutyothapibal & Shenandi'),
    'To Be Young Again': (21, 'Demian Sims & Shenandi'),
    'Playing in the Sun': (25, 'Eric Kaye & Shenandi'),
    'March of the Puffins': (27, 'Vinnie Zummo'),
    'The Kitchen Sink': (64, 'Deborah Nadine Hurwitz'),
    'Clown Wedding': (48, 'Craig Stuart Garfinkle'),
    'Escape From Preschool': (75, 'Nick Seeley & Shenandi'),
    'Ethereal Vibes': (30, None),
}

changed = []
files = list(Path(ROOT / '罐頭音樂研究所' / '巧連智').rglob('index.html')) + \
        list(Path(ROOT / '使用公司').rglob('index.html'))

for f in files:
    h = f.read_text(encoding='utf-8')
    orig = h
    for title, (no, comp) in MAP.items():
        url = f'{BASE}{no}'

        def repl(m, url=url, title=title, comp=comp):
            href, attrs, tail = m.group(1), m.group(2), m.group(3)
            # 只改 YouTube 或已是 diner 的連結，其他廠牌連結不動
            if 'thedinermusic.com' not in href and 'youtube.com' not in href:
                return m.group(0)
            text = f'{title} - {comp}' if comp else f'{title}{tail}'
            return f'<a href="{url}"{attrs}>{text}</a>'

        pat = re.compile(r'<a href="([^"]+)"([^>]*)>' + re.escape(title) + r'([^<]*)</a>')
        h = pat.sub(repl, h)
    if h != orig:
        f.write_text(h, encoding='utf-8')
        changed.append(f.parent.name)

print('patched pages:', len(changed))
for c in changed:
    print(' -', c)
