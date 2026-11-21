#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO童話世界 第18集 大寶與二寶／紅小鳥的魔豆
- 大寶與二寶：Alf And Edna、Dashing Desmond 各加一個 哥哥姐姐 框（既有 Frank Stamp 框不動）
- 紅小鳥的魔豆：Come And Play、Lazybones、Coconut Calypso 各加一個 哥哥姐姐 框（原地加框、曲序不動）
幂等：結構已正確則跳過。
"""
import re, sys, os, html as _html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/yoyo童話世界-第18集-大寶與二寶紅小鳥的魔豆/index.html')

EXPECT = ['Frank Stamp', 'Alf And Edna', 'Dashing Desmond', 'Come And Play', 'Connemara Hills',
          'Booraye', 'Knockanore Hill', 'Village Scene', 'Lazybones', 'Spring Air', 'A Wee Dram',
          'Coconut Calypso']


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
    parts.append(UNIT('大寶與二寶') + ' ' + SM + ' ' + UL(['Frank Stamp']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Alf And Edna']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Dashing Desmond']))
    parts.append(BL)
    parts.append(AD + ' ')
    parts.append(UNIT('紅小鳥的魔豆') + ' ' + SM + ' ' + UL(['Come And Play']))
    parts.append(BL)
    parts.append(UL(['Connemara Hills', 'Booraye', 'Knockanore Hill', 'Village Scene']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Lazybones']))
    parts.append(BL)
    parts.append(UL(['Spring Air', 'A Wee Dram']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Coconut Calypso'], extra=blankli + outro))
    new_body = ''.join(parts)

    new = head + new_body + '</main>' + tail
    if new == h:
        print('結構已正確，跳過')
        return
    open(PAGE, 'w', encoding='utf-8').write(new)
    print('已更新 ep18：大寶與二寶 +2 框、紅小鳥的魔豆 +3 框（全頁 6 框）')


if __name__ == '__main__':
    main()
