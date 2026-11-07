#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-11-07 孝瓏：左欄改成「就地展開」（品牌 → 專輯 → 曲目），移除底部另開的 tree-h 區塊。
以 href（目錄路徑）比對當前節點，不用名稱比對。
用法：python3 tree_inline_expand2.py <lib_dir> [--dry]
"""
import os, re, sys, glob, urllib.parse

LIB = sys.argv[1] if len(sys.argv) > 1 else '.'
DRY = '--dry' in sys.argv

SEC = re.compile(r'<div class="tree-h(?:[^"]*)"[^>]*>(.*?)</div><ul class="tree"[^>]*>(.*?)</ul>', re.S)


def enc_variants(seg):
    out = {seg, urllib.parse.quote(seg), urllib.parse.quote(seg, safe='')}
    return out


def href_matches(href, seg):
    """href 是否指向 segment 目錄（容忍前面相對路徑與結尾 slash）"""
    h = href.rstrip('/')
    if seg in h.split('/'):
        return True
    for v in enc_variants(seg):
        if v in h.split('/'):
            return True
    return False


def inline(html, seg, sub_html):
    """在 html 中找指向 seg 的 li（class 含 cur）→ 塞入 sub_html 就地展開"""
    lis = re.findall(r'<li class="cur[^"]*"><a ([^>]*)>(.*?)</a></li>', html, re.S)
    for attrs, name in lis:
        m = re.search(r'href="([^"]+)"', attrs)
        if not m:
            continue
        if href_matches(m.group(1), seg):
            pat = re.compile(r'<li class="cur[^"]*"><a ' + re.escape(attrs) + r'>' + re.escape(name) + r'</a></li>')
            mm = pat.search(html)
            if not mm:
                continue
            new = ('<li class="cur open"><span class="arw">\u25be</span><a %s>%s</a>'
                   '<ul class="tree sub">%s</ul></li>' % (attrs, name, sub_html))
            return html[:mm.start()] + new + html[mm.end():]
    return None


def process(path):
    s = open(path, encoding='utf-8').read()
    i, j = s.find('<aside'), s.find('</aside>')
    if i < 0 or j < 0:
        return 'no-aside'
    aside = s[i:j]
    secs = list(SEC.finditer(aside))
    if len(secs) < 2:
        return 'skip'
    rel = os.path.relpath(os.path.dirname(path), LIB).split(os.sep)
    # rel: [brand] / [brand, album] / [brand, album, track]
    brand = rel[0]
    album = rel[1] if len(rel) >= 2 else None
    brand_list = secs[0].group(2)
    album_list = secs[1].group(2)
    if len(secs) >= 3 and album:
        track_list = secs[2].group(2)
        merged = inline(album_list, album, track_list)
        if merged is None:
            return 'no-cur(album)'
        album_list = merged
    merged = inline(brand_list, brand, album_list)
    if merged is None:
        return 'no-cur(brand)'
    brand_list = merged
    first = secs[0]
    new_aside = aside[:first.start()] + first.group(0).replace(first.group(2), brand_list, 1) + aside[secs[-1].end():]
    out = s[:i] + new_aside + s[j:]
    if not DRY:
        open(path, 'w', encoding='utf-8').write(out)
    return 'ok'


if __name__ == '__main__':
    files = glob.glob(os.path.join(LIB, '**', 'index.html'), recursive=True)
    from collections import Counter
    c = Counter()
    bad = []
    for p in files:
        r = process(p)
        c[r] += 1
        if r.startswith('no-cur'):
            bad.append((p, r))
    print('檔案', len(files), dict(c))
    for b in bad[:10]:
        print(' !', b[1], b[0])
