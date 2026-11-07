#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-11-07 孝瓏：左欄改成「就地展開」（品牌 → 專輯 → 曲目），
移除底部另開的 tree-h 區塊。
用法：python3 tree_inline_expand.py <root_dir> [--dry]
"""
import os, re, sys, glob

LIB = sys.argv[1] if len(sys.argv) > 1 else '.'
DRY = '--dry' in sys.argv

SEC = re.compile(r'<div class="tree-h(?:[^"]*)"[^>]*>(.*?)</div><ul class="tree"[^>]*>(.*?)</ul>', re.S)
CUR = re.compile(r'<li class="cur"><a ([^>]*)>([^<]*)</a></li>')

def inline(cur_html, name, sub_html):
    """把 sub_html 塞進 cur_html 中名為 name 的 li，就地展開"""
    pat = re.compile(r'<li class="cur"><a ([^>]*)>' + re.escape(name) + r'</a></li>')
    m = pat.search(cur_html)
    if not m:
        return None
    new = '<li class="cur open"><span class="arw">\u25be</span><a %s>%s</a><ul class="tree sub">%s</ul></li>' % (m.group(1), name, sub_html)
    return cur_html[:m.start()] + new + cur_html[m.end():]

def process(path):
    s = open(path, encoding='utf-8').read()
    i = s.find('<aside')
    j = s.find('</aside>')
    if i < 0 or j < 0:
        return 'no-aside'
    aside = s[i:j]
    secs = list(SEC.finditer(aside))
    if len(secs) < 2:
        return 'skip(secs=%d)' % len(secs)
    # 名稱：第一段是「音樂圖書館」（品牌清單），其餘是品牌/專輯
    blocks = [(re.sub(r'<[^>]+>', '', m.group(1)).strip(), m.group(2)) for m in secs]
    if blocks[0][0] != '音樂圖書館':
        return 'skip(first=%s)' % blocks[0][0]
    brand_list = blocks[0][1]
    # 由內而外合併
    if len(blocks) >= 3:
        album_name, track_list = blocks[2][0], blocks[2][1]
        album_list = blocks[1][1]
        merged = inline(album_list, album_name, track_list)
        if merged is None:
            return 'no-cur(album=%s)' % album_name
        album_list = merged
    else:
        album_list = blocks[1][1]
    brand_name = blocks[1][0]
    merged = inline(brand_list, brand_name, album_list)
    if merged is None:
        return 'no-cur(brand=%s)' % brand_name
    brand_list = merged
    # 重建 aside：tree-h 音樂圖書館 + 品牌清單（其餘段落移除）
    first = secs[0]
    new_aside = aside[:first.start()] + first.group(0).replace(first.group(2), brand_list, 1) + aside[secs[-1].end():]
    out = s[:i] + new_aside + s[j:]
    if not DRY:
        open(path, 'w', encoding='utf-8').write(out)
    return 'ok'

if __name__ == '__main__':
    files = [p for p in glob.glob(os.path.join(LIB, '**', 'index.html'), recursive=True)]
    from collections import Counter
    c = Counter()
    bad = []
    for p in files:
        r = process(p)
        key = r.split('(')[0]
        c[key] += 1
        if key not in ('ok', 'skip'):
            bad.append((p, r))
    print('檔案', len(files), dict(c))
    for b in bad[:15]:
        print(' !', b[1], b[0])
