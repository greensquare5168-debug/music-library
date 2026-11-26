#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修「使用作品」被砍成上層名稱（2026-11-26 孝瓏回報）

症狀：連結 href 指向集頁，但文字只剩上層名稱（例：「YOYO嘻遊記 第05季 第04集 好山好水 好好玩台東」→「YOYO嘻遊記 第05季」）
肇因：commit 2e9c0ddb 的名稱推導把「季目錄」當成目標頁。

修法：以 href 指向的目錄 → 讀該頁 index.html 的 <title>（去掉「｜圖書館音樂研究所」）當正式名稱。
     只改「文字與目標 title 不一致且現文字是 title 的前綴／子字串」的項目（＝明顯被砍短），
     其他不動（尊重人工命名）。

用法： python3 fix_entries_truncated_names_20261126.py [--dry-run]
"""
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv

ENTRIES_RE = re.compile(r'(<ul class="entries">)(.*?)(</ul>)', re.S)
LI_RE = re.compile(r'<li[^>]*>.*?</li>', re.S)
A_RE = re.compile(r'<a href="([^"]+)"([^>]*)>(.*?)</a>', re.S)

_title_cache = {}


def page_title(absdir):
    if absdir in _title_cache:
        return _title_cache[absdir]
    idx = os.path.join(absdir, 'index.html')
    t = None
    if os.path.isfile(idx):
        h = open(idx, encoding='utf-8').read()
        m = re.search(r'<title>(.*?)</title>', h, re.S)
        if m:
            t = re.split(r'\s*[｜|]\s*', m.group(1).strip())[0].strip()
    _title_cache[absdir] = t
    return t


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s).strip()


fixed = pages = 0
samples = []

for dirpath, _, fs in os.walk(ROOT):
    if 'index.html' not in fs:
        continue
    path = os.path.join(dirpath, 'index.html')
    h = open(path, encoding='utf-8').read()
    m = ENTRIES_RE.search(h)
    if not m:
        continue
    body = m.group(2)
    new_body = body
    for li in LI_RE.findall(body):
        am = A_RE.search(li)
        if not am:
            continue
        href, attrs, inner = am.group(1), am.group(2), am.group(3)
        if 'class="lbl"' in inner and strip_tags(inner).count('（') >= 2:
            pass
        # 只處理「連結文字」部分（第一個 <a> 內的純文字）
        name = strip_tags(inner)
        if not name:
            continue
        if href.startswith('/music-library/'):
            rel = urllib.parse.unquote(href[len('/music-library/'):]).rstrip('/')
            absdir = os.path.join(os.getcwd(), rel)
        elif href.startswith('http'):
            continue
        else:
            rel = os.path.normpath(os.path.join(dirpath, urllib.parse.unquote(href))).rstrip('/')
            absdir = os.path.join(os.getcwd(), rel)
        title = page_title(absdir)
        if not title or title == name:
            continue
        # 只修「被砍短」：現名是正式名的前綴／去掉標點後是子字串
        n_norm = re.sub(r'[\s／/·_\-－—]', '', name)
        t_norm = re.sub(r'[\s／/·_\-－—]', '', title)
        if not (title.startswith(name) or n_norm in t_norm):
            continue
        # 保留可能的 <span class="lbl">…</span> 等原標記
        lbl = ''
        m_lbl = re.search(r'<span class="lbl">.*?</span>', inner, re.S)
        if m_lbl:
            lbl = m_lbl.group(0)
            inner_rest = inner.replace(lbl, '')
        else:
            inner_rest = inner
        # inner_rest 內的第一段純文字取代為 title
        new_inner = inner_rest.replace(name, title, 1) + lbl if lbl else inner_rest.replace(name, title, 1)
        new_a = f'<a href="{href}"{attrs}>{new_inner}</a>'
        new_li = li.replace(am.group(0), new_a, 1)
        new_body = new_body.replace(li, new_li, 1)
        fixed += 1
        if len(samples) < 12:
            samples.append((os.path.relpath(path, BASE), name, title))
    if new_body != body:
        pages += 1
        if not DRY:
            open(path, 'w', encoding='utf-8').write(
                h[:m.start()] + m.group(1) + new_body + m.group(3) + h[m.end():])

print(f'{"[DRY] " if DRY else ""}修 {fixed} 處，涉及 {pages} 頁')
for p, a, b in samples:
    print(f'  {p[-55:]}  {a[:18]} → {b[:34]}')
