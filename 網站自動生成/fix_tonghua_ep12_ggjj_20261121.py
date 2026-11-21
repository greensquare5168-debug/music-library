#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO童話世界 第12集 螢光森林／花花找朋友
- 螢光森林：Dark Planet、Village Playground 各一個 哥哥姐姐 框（既有 Marching About 框不動）
- 花花找朋友：Tune For Toon、Rainy Day（後）各一個 哥哥姐姐 框
- Village Playground（花花找朋友那段的重複紀錄）位置錯誤（在 Rainy Day 框下面）→ 移到 Rainy Day 框上面
幂等：結構已正確則跳過。
"""
import re, sys, os, html as _html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/yoyo童話世界-第12集-螢光森林花花找朋友/index.html')

EXPECT = ['Marching About', 'Playtime', 'Dark Planet', 'Village Playground', 'Village Playground',
          'Tune For Toon', "Swingin' George", 'Rainy Day']


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
    vp = []          # Village Playground 的兩筆（第一筆＝螢光森林、第二筆＝花花找朋友）
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
            if t == 'Village Playground':
                vp.append(li)
                order.append('Village Playground#%d' % len(vp))
            else:
                tracks[t] = li
                order.append(t)

    got = [t if not t.startswith('Village Playground#') else 'Village Playground' for t in order]
    if sorted(got) != sorted(EXPECT):
        print('曲目集合不符，實際：', order)
        sys.exit(1)
    if len(vp) != 2:
        print('Village Playground 筆數異常：', len(vp))
        sys.exit(1)

    VP_FOREST, VP_GIRL = vp[0], vp[1]

    def UL(titles, extra=''):
        return '<ul class="entries">' + ''.join(tracks[t] for t in titles) + extra + '</ul>'

    def UNIT(label):
        return '<div class="unit" data-label="%s">%s</div>' % (label, label)

    SM = '<div class="unit sm" data-label="哥哥姐姐">哥哥姐姐</div>'
    BL = '<div class="blankline">&nbsp;</div>'
    m = re.search(r'<div class="unit ad"[^>]*>廣告後片段</div>', body)
    AD = m.group(0) if m else '<div class="unit ad" data-label="廣告後片段">廣告後片段</div>'

    parts = ['<ul class="entries">' + intro + '</ul>', BL]
    # 螢光森林：Marching About（既有框）→ Playtime → Dark Planet（框）→ Village Playground（框）
    parts.append(UNIT('螢光森林') + ' ' + SM + ' ' + UL(['Marching About']))
    parts.append(BL)
    parts.append(UL(['Playtime']))
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Dark Planet']))
    parts.append(BL)
    parts.append(SM + ' <ul class="entries">' + VP_FOREST + '</ul>')
    parts.append(BL)
    parts.append(AD + ' ')
    # 花花找朋友：Tune For Toon（框）→ Swingin' George／Village Playground → Rainy Day（框，後）
    parts.append(UNIT('花花找朋友') + ' ' + SM + ' ' + UL(['Tune For Toon']))
    parts.append(BL)
    parts.append('<ul class="entries">' + tracks["Swingin' George"] + VP_GIRL + '</ul>')
    parts.append(BL)
    parts.append(SM + ' ' + UL(['Rainy Day'], extra=blankli + outro))
    new_body = ''.join(parts)

    new = head + new_body + '</main>' + tail
    if new == h:
        print('結構已正確，跳過')
        return
    open(PAGE, 'w', encoding='utf-8').write(new)
    print('已更新 ep12：螢光森林 +2 框、花花找朋友 +2 框、Village Playground 移到 Rainy Day 框上面')


if __name__ == '__main__':
    main()
