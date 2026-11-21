#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第13集 曲目頁新增使用紀錄（小小姑娘 哥哥姐姐）
- Downside Up：插在 第07集 之前
- Foxy Trot：接在 第07集 之後
- Walkin' And Whistlin'：清單末端（童話世界 排在小狀元/嘻遊記之後）
幂等：已有 ep13 列就跳過。
"""
import os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, '罐頭音樂研究所/圖書館音樂')
EP13 = 'yoyo%E7%AB%A5%E8%A9%B1%E4%B8%96%E7%95%8C-%E7%AC%AC13%E9%9B%86'
EP07 = 'yoyo%E7%AB%A5%E8%A9%B1%E4%B8%96%E7%95%8C-%E7%AC%AC07%E9%9B%86'
EP13_URL = ('/music-library/%E7%BD%90%E9%A0%AD%E9%9F%B3%E6%A8%82%E7%A0%94%E7%A9%B6%E6%89%80/yoyotv/'
            + EP13 + '-%E9%B4%A8%E5%AA%BD%E5%AA%BD%E7%9A%84%E5%AF%B6%E8%B2%9D%E8%9B%8B%E5%B0%8F%E5%B0%8F%E5%A7%91%E5%A8%98/')
LI = ('<li><a href="' + EP13_URL + '">YOYO童話世界 第13集 鴨媽媽的寶貝蛋／小小姑娘</a>'
      '<span class="lbl">（小小姑娘 哥哥姐姐）</span></li>')

JOBS = [
    ('parry/pml148-comicals/downside-up-jonathan-jans', 'before', EP07),
    ('parry/pml148-comicals/foxy-trot-james-clarke', 'after', EP07),
    ('parry/pml016-the-comedy-collection/walkin-and-whistlin-harry-gordon-forbes', 'append', None),
]

# 既有的 ep13 連結長度可能不同（各頁網址寫法一致），用「第13集 鴨媽媽」字樣判斷
for rel, where, anchor in JOBS:
    p = os.path.join(LIB, rel, 'index.html')
    h = open(p, encoding='utf-8').read()
    if 'YOYO童話世界 第13集 鴨媽媽的寶貝蛋／小小姑娘' in h:
        print('已有 ep13 列，跳過：', rel)
        continue
    i = h.find('</iframe>')
    ul_s = h.rfind('<ul class="entries">', 0, i)   # 使用作品 ul 從 iframe 之前就開始
    ul_e = h.find('</ul>', i)
    ul = h[ul_s:ul_e]
    if where in ('before', 'after'):
        m = re.search(r'<li><a href="[^"]*' + anchor + r'[^"]*".*?</li>', ul, re.S)
        if not m:
            print('找不到錨點（%s）：%s' % (anchor[:20], rel))
            continue
        pos = m.start() if where == 'before' else m.end()
        new_ul = ul[:pos] + LI + ul[pos:]
    else:
        new_ul = ul + LI
    out = h[:ul_s] + new_ul + h[ul_e:]
    open(p, 'w', encoding='utf-8').write(out)
    print('已加入 ep13 使用紀錄：', rel, '(%s)' % where)
