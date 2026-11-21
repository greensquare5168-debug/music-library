#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO童話世界 第13集 鴨媽媽的寶貝蛋／小小姑娘
1) Fools Errand 原誤放「小小姑娘」→ 搬回「鴨媽媽的寶貝蛋」（中段，Drunken Waltz 之後、Hip Swing 之前）
2) Fools Errand、Hip Swing 各自獨立一個「哥哥姐姐」框（原地加框、其餘曲序不動）
幂等：重跑結構相同則跳過。
"""
import re, sys, os, html as _html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/yoyo童話世界-第13集-鴨媽媽的寶貝蛋小小姑娘/index.html')

# 允許的現況（修好前的舊結構 / 修好後的新結構）
EXPECT = [
    'Drunken Waltz', 'Hip Swing', 'Fools Errand',
]

def li_title(li):
    m = re.search(r'>([^<>]+)</a>', li)
    t = m.group(1).strip() if m else ''
    for sep in (' - ', ' – '):
        if sep in t:
            t = t.split(sep)[0].strip()
    return t

def main():
    h = open(PAGE, encoding='utf-8').read()

    head, rest = h.split('<ul class="entries">', 1)
    body, tail = rest.split('</main>', 1)

    lis = re.findall(r'<li[^>]*>.*?</li>', body, re.S)
    intro = outro = blankli = None
    tracks, order = {}, []
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

    if sorted(order) != sorted(EXPECT):
        print('曲目集合不符，實際：', order)
        sys.exit(1)

    def UL(titles, extra=''):
        return '<ul class="entries">' + ''.join(tracks[t] for t in titles) + extra + '</ul>'

    def UNIT(label):
        return '<div class="unit" data-label="%s">%s</div>' % (label, label)

    SM = '<div class="unit sm" data-label="哥哥姐姐">哥哥姐姐</div>'
    BL = '<div class="blankline">&nbsp;</div>'
    m = re.search(r'<div class="unit ad"[^>]*>廣告後片段</div>', body)
    AD = m.group(0) if m else '<div class="unit ad" data-label="廣告後片段">廣告後片段</div>'

    parts = ['<ul class="entries">' + intro + '</ul>', BL]
    # 鴨媽媽的寶貝蛋：上 Drunken Waltz → 中 Fools Errand → 下 Hip Swing（各自 哥哥姐姐 框）
    parts.append(UNIT('鴨媽媽的寶貝蛋') + ' ' + SM + ' ' + UL(['Drunken Waltz']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Fools Errand']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Hip Swing']))
    parts.append(BL)
    parts.append(AD + ' ')
    # 小小姑娘：目前已無曲目（僅片尾）
    parts.append(UNIT('小小姑娘') + ' ' + UL([], extra=(blankli or '') + outro))
    new_body = ''.join(parts)

    new = head + new_body + '</main>' + tail
    if new == h:
        print('結構已正確，跳過')
        return
    open(PAGE, 'w', encoding='utf-8').write(new)
    print('已更新 ep13：Fools Errand 搬回鴨媽媽的寶貝蛋（中段）＋ Fools Errand/Hip Swing 加哥哥姐姐框')

if __name__ == '__main__':
    main()
