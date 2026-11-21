#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO童話世界 第06集 自以為是的小波／一起去旅行
1) 自以為是的小波：Hat & Cane、Spring Song 各自獨立一個「哥哥姐姐」框（原地加框、曲序不動）
2) 一起去旅行：Rag & Bones、To & Fro、A Dozen Roses 各自獨立一個「哥哥姐姐」框
3) 夕暮れサバンナのキリン 專輯更正：（2 ジングル・ブリッジ）→（NSF-259 Animal Paradise），並移除錯誤的站內 ↗ 連結
幂等：重跑結構相同則跳過。
"""
import re, sys, os, html as _html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/yoyo童話世界-第06集-自以為是的小波一起去旅行/index.html')

EXPECT = [
    'Roly-Poly', 'Whimsy', 'Christmas Dawn', "Just Ramblin'", '夕暮れサバンナのキリン',
    "I'm Lost", 'Hat & Cane', 'Sorrow', 'Busy Beehive', 'Lullaby', 'Brighton Run', 'Downside Up',
    'Lullabye', 'Kids on Parade', 'Spring Song', 'Rag & Bones', 'To & Fro', 'A Dozen Roses',
]

def li_title(html):
    m = re.search(r'>([^<>]+)</a>', html)
    t = m.group(1).strip() if m else ''
    for sep in (' - ', ' – '):
        if sep in t:
            t = t.split(sep)[0].strip()
    return t

def main():
    h = open(PAGE, encoding='utf-8').read()

    head, rest = h.split('<ul class="entries">', 1)
    body, tail = rest.split('</main>', 1)

    # 取出所有 li（含空白 li / 片尾 li）
    lis = re.findall(r'<li[^>]*>.*?</li>', body, re.S)
    intro = None
    outro = None
    blankli = None
    tracks = {}
    order = []
    for li in lis:
        if 'class="r-intro"' in li:
            intro = li
        elif 'class="r-outro"' in li:
            outro = li
        elif 'class="blankline"' in li:
            blankli = li
        else:
            t = _html.unescape(li_title(li))
            tracks[t] = li
            order.append(t)

    got = [t for t in order]
    norm = lambda xs: [re.sub(r'\s+', ' ', x).replace('&amp;', '&').replace('’', "'").strip() for x in xs]
    if norm(got) != norm(EXPECT):
        print('曲目順序/名稱不符')
        for a, b in zip(norm(got), norm(EXPECT)):
            if a != b:
                print('  got=%r expect=%r' % (a, b))
        print('got 全部：', got)
        sys.exit(1)

    # 3) 修正 夕暮れサバンナのキリン 的專輯標示 + 移除錯誤站內連結
    k = '夕暮れサバンナのキリン'
    li = tracks[k]
    li = re.sub(r'（2 ジングル・ブリッジ）', '（NSF-259 Animal Paradise）', li)
    li = re.sub(r'<a class="same" href="[^"]*on-jiten[^"]*"[^>]*>↗</a>', '', li)
    tracks[k] = li

    def UL(titles, extra=''):
        return '<ul class="entries">' + ''.join(tracks[t] for t in titles) + extra + '</ul>'

    def UNIT(label):
        return '<div class="unit" data-label="%s">%s</div>' % (label, label)

    SM = '<div class="unit sm" data-label="哥哥姐姐">哥哥姐姐</div>'
    BL = '<div class="blankline">&nbsp;</div>'
    AD = ('<div class="unit ad" data-label="廣告後片段" style="display:block;text-align:center;border:none;'
          'border-bottom:2px solid #8fa3bd;border-radius:0;background:none;padding:2px 0 8px;font-weight:400;'
          'color:#2b3648;font-size:13px">廣告後片段</div>')

    ad_old = re.search(r'<div class="unit ad"[^>]*>廣告後片段</div>', body)
    if ad_old:
        AD = ad_old.group(0)

    parts = []
    parts.append('<ul class="entries">' + intro + '</ul>')
    parts.append(BL)
    # 自以為是的小波
    parts.append(UNIT('自以為是的小波') + ' ' + SM + ' ' + UL(['Roly-Poly']))
    parts.append(BL)
    parts.append(UL(['Whimsy', 'Christmas Dawn', "Just Ramblin'", k, "I'm Lost"]))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Hat & Cane']))
    parts.append(BL)
    parts.append(UL(['Sorrow', 'Busy Beehive', 'Lullaby', 'Brighton Run', 'Downside Up', 'Lullabye', 'Kids on Parade']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Spring Song']))
    parts.append(BL)
    parts.append(AD + ' ')
    # 一起去旅行
    parts.append(UNIT('一起去旅行') + ' ' + SM + ' ' + UL(['Rag & Bones']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['To & Fro']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['A Dozen Roses'], extra=blankli + outro))
    new_body = ''.join(parts)

    new = head + new_body + '</main>' + tail
    if new == h:
        print('結構已正確，跳過')
        return
    open(PAGE, 'w', encoding='utf-8').write(new)
    print('已更新 ep06：3 個 自以為是的小波 哥哥姐姐框 + 3 個 一起去旅行 哥哥姐姐框 + 夕暮れ 專輯更正')

if __name__ == '__main__':
    main()
