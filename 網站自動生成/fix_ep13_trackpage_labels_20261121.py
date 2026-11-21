#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第13集 曲目頁「使用作品」標記更正（鴨媽媽的寶貝蛋 哥哥姐姐）
- Fools Errand：（小小姑娘）→（鴨媽媽的寶貝蛋 哥哥姐姐）
- Hip Swing：（鴨媽媽的寶貝蛋）→（鴨媽媽的寶貝蛋 哥哥姐姐）
幂等：已是目標值就跳過。
"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, '罐頭音樂研究所/圖書館音樂')
EP13 = 'yoyo%E7%AB%A5%E8%A9%B1%E4%B8%96%E7%95%8C-%E7%AC%AC13%E9%9B%86'

JOBS = [
    ('bruton-vaults/bv075-all-for-laughs/fools-errand-john-valmore-pearson', '（小小姑娘）', '（鴨媽媽的寶貝蛋 哥哥姐姐）'),
    ('parry/pml148-comicals/hip-swing-eric-allen', '（鴨媽媽的寶貝蛋）', '（鴨媽媽的寶貝蛋 哥哥姐姐）'),
]

for rel, old, new in JOBS:
    p = os.path.join(LIB, rel, 'index.html')
    h = open(p, encoding='utf-8').read()
    pat = re.compile(r'(<li><a href="/music-library/[^"]*' + EP13 + r'[^"]*"[^>]*>[^<]*</a>)<span class="lbl">([^<]*)</span>(</li>)')
    m = pat.search(h)
    if not m:
        print('找不到 ep13 列：', rel)
        continue
    cur = m.group(2)
    if cur == new:
        print('已正確，跳過：', rel)
        continue
    if cur != old:
        print('目前標記非預期（%s），人工確認：%s' % (cur, rel))
        continue
    out = h[:m.start()] + m.group(1) + '<span class="lbl">' + new + '</span>' + m.group(3) + h[m.end():]
    open(p, 'w', encoding='utf-8').write(out)
    print('已更正：', rel, old, '→', new)
