#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第06集 曲目頁「使用作品」標記（自以為是的小波／一起去旅行 哥哥姐姐）
幂等：已有標記就跳過。
"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, '罐頭音樂研究所/圖書館音樂')

MAP = {
    'match/mat158-comedy-store/hat-cane-stephen-paul-martin': '自以為是的小波 哥哥姐姐',
    'match/mat158-comedy-store/spring-song-david-john-hynes': '自以為是的小波 哥哥姐姐',
    'match/mat158-comedy-store/rag-bones-stephen-paul-martin': '一起去旅行 哥哥姐姐',
    'metro/mmp031-comedy-fun/to-fro-thomas-foyer': '一起去旅行 哥哥姐姐',
    'koka/kok2139-smile/a-dozen-roses-armand-michel-frydman': '一起去旅行 哥哥姐姐',
}
EP06 = 'yoyo%E7%AB%A5%E8%A9%B1%E4%B8%96%E7%95%8C-%E7%AC%AC06%E9%9B%86'

for rel, label in MAP.items():
    p = os.path.join(LIB, rel, 'index.html')
    h = open(p, encoding='utf-8').read()
    pat = re.compile(r'(<li><a href="/music-library/[^"]*' + EP06 + r'[^"]*"[^>]*>[^<]*</a>)(<span class="lbl">（[^<]*）</span>)?(</li>)')
    m = pat.search(h)
    if not m:
        print('找不到 ep06 列：', rel)
        continue
    if m.group(2):
        print('已有標記，跳過：', rel)
        continue
    new = h[:m.start()] + m.group(1) + '<span class="lbl">（%s）</span>' % label + m.group(3) + h[m.end():]
    open(p, 'w', encoding='utf-8').write(new)
    print('已標記：', rel, '→', label)
