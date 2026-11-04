#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Tiptoes - Robert Guerrier 記錄為「有使用」：
- 使用頁面：巧連智低年級版 2012年11月號 知識閱讀本CD 一起去觀光農場（插在 Precious Comedy 與 Comedy Cue 之間）
- 曲目頁：使用頁面清單加入該頁、移除「（尚未發現使用作品）」
- 專輯頁：Tiptoes 那列 mark-x → ✓
- search-index：該曲 ✕ → ✓
"""
from pathlib import Path
from urllib.parse import quote
import json
import re

ROOT = Path(__file__).resolve().parent.parent
LIB = '罐頭音樂研究所/圖書館音樂'
PAGE = '罐頭音樂研究所/巧連智/低年級版/巧連智低年級版cd/巧連智低年級版2012年11月號cd-一起去觀光農場'
PAGE_NAME = '巧連智低年級版 2012年11月號 知識閱讀本CD 一起去觀光農場'
TRACK_SLUG = 'tiptoes-robert-guerrier'
ALBUM = 'music-for-productions/mfpl-20-best-of-film-scores'

abs_p = lambda *parts: '/music-library/' + '/'.join(quote(p) for p in parts) + '/'
page_abs = abs_p(*PAGE.split('/'))
track_abs = abs_p(LIB, *ALBUM.split('/'), TRACK_SLUG)

MARK_OK = ('<span class="mark" title="有發現使用作品" style="display:inline-flex;align-items:center;'
           'justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px;'
           'background:#eaf7ef;color:#12894a;border:1px solid #bfe6cd">✓</span>')

# 1) 使用頁面插入曲目
p = ROOT / PAGE / 'index.html'
s = p.read_text(encoding='utf-8')
if 'Tiptoes - Robert Guerrier' not in s:
    anchor = re.search(r'<li><a href="[^"]*"[^>]*>Precious Comedy - Marc Dall&#x27;Anese</a></li>', s)
    if not anchor:
        anchor = re.search(r'<li><a href="[^"]*"[^>]*>Precious Comedy - Marc Dall\'Anese</a></li>', s)
    if not anchor:
        raise SystemExit('找不到 Precious Comedy 那一列')
    new_li = f'<li><a href="{track_abs}">Tiptoes - Robert Guerrier</a></li>'
    s = s[:anchor.end()] + new_li + s[anchor.end():]
    p.write_text(s, encoding='utf-8')
    print('使用頁面：已插入 Tiptoes（Precious Comedy 之後）')
else:
    print('使用頁面：已存在 Tiptoes')

# 2) 曲目頁：加使用頁面、去掉「尚未發現使用作品」
p = ROOT / LIB / ALBUM / TRACK_SLUG / 'index.html'
s = p.read_text(encoding='utf-8')
if PAGE_NAME not in s:
    entry = f'<ul class="entries"><li><a href="{page_abs}">{PAGE_NAME}</a></li></ul>'
    s = s.replace('<p class="muted">（尚未發現使用作品）</p>', entry, 1)
    p.write_text(s, encoding='utf-8')
    print('曲目頁：已加入使用頁面')
else:
    print('曲目頁：已有使用頁面')

# 3) 專輯頁 Tiptoes 列改 ✓
p = ROOT / LIB / ALBUM / 'index.html'
s = p.read_text(encoding='utf-8')
if 'tiptoes-robert-guerrier' not in s:
    raise SystemExit('專輯頁找不到 Tiptoes 列')
m = re.search(r'(<li><a class="row" href="[^"]*tiptoes-robert-guerrier/">.*?)<span class="mark mark-x"[^>]*>✕</span>', s, re.S)
if m:
    s = s[:m.start()] + m.group(1) + MARK_OK + s[m.end():]
    p.write_text(s, encoding='utf-8')
    print('專輯頁：Tiptoes 已標記 ✓')
else:
    print('專輯頁：Tiptoes 已是 ✓ 或格式不同')

# 4) search-index：✕ → ✓
p = ROOT / 'search-index.json'
idx = json.loads(p.read_text(encoding='utf-8'))
n = 0
for e in idx:
    if e.get('k') and 'Tiptoes - Robert Guerrier✕' in e['k']:
        e['k'] = e['k'].replace('Tiptoes - Robert Guerrier✕', 'Tiptoes - Robert Guerrier✓')
        n += 1
p.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
print(f'search-index：更新 {n} 筆')
