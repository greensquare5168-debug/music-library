#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曲目頁「使用作品」按網站排法重排（2026-11-26 孝瓏指示）

排法＝該品牌／節目 index 頁的顯示順序（孝瓏 2026-11-17 鐵則 §1）：
  以作品所屬「節目／系列目錄」的 index.html 中條目出現順序為 key。
  - 優先讀該目錄頁的 <span class="rn"> / a.row title（集頁清單）
  - 讀不到則退回目錄底下的資料夾名稱排序

用法：
  python3 fix_entries_order_20261126.py --dry-run
  python3 fix_entries_order_20261126.py --file <某頁 index.html>
"""
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv
ONLY = None
if '--file' in sys.argv:
    ONLY = sys.argv[sys.argv.index('--file') + 1]

ENTRIES_RE = re.compile(r'(<ul class="entries">)(.*?)(</ul>)', re.S)
LI_RE = re.compile(r'<li[^>]*>.*?</li>', re.S)

_order_cache = {}


def find_series(t_rel):
    """作品可能在 節目/系列/集 或 節目/集 → 找「有兄弟目錄且含 index.html 清單」的最長前綴"""
    parts = t_rel.split(os.sep)
    for cut in range(len(parts) - 1, 0, -1):
        cand = os.sep.join(parts[:cut])
        if os.path.isfile(os.path.join(cand, 'index.html')):
            return cand
    return os.path.dirname(t_rel)


def _load_order(series_rel):
    if series_rel in _order_cache:
        return _order_cache[series_rel]
    idx = os.path.join(series_rel, 'index.html')
    order = {}
    if os.path.isfile(idx):
        h = open(idx, encoding='utf-8').read()
        hrefs = re.findall(r'<a class="row"[^>]*href="([^"]+)"', h)
        if not hrefs:
            hrefs = re.findall(r'<a href="([^"]+)"[^>]*><span class="rn">', h)
        n = 0
        for hf in hrefs:
            t = os.path.normpath(os.path.join(series_rel, urllib.parse.unquote(hf))).rstrip('/')
            if t not in order:
                order[t] = n
                n += 1
    _order_cache[series_rel] = order
    return order


def dir_order(series_rel):
    return _load_order(series_rel)


def fix_page(path):
    page_rel = os.path.dirname(os.path.relpath(path, os.getcwd()))
    h = open(path, encoding='utf-8').read()
    m = ENTRIES_RE.search(h)
    if not m:
        return 0
    body = m.group(2)
    items = LI_RE.findall(body)
    if len(items) < 2:
        return 0

    keys = []
    for li in items:
        am = re.search(r'<a href="([^"]+)"', li)
        if not am:
            keys.append((10 ** 6, li))
            continue
        href = am.group(1)
        if href.startswith('/music-library/'):
            t = urllib.parse.unquote(href[len('/music-library/'):]).rstrip('/')
            t_rel = os.path.relpath(os.path.join(os.getcwd(), t), os.getcwd())
        else:
            t_rel = os.path.normpath(os.path.join(page_rel, urllib.parse.unquote(href))).rstrip('/')
        # 找最長存在的前綴目錄（作品集頁本身在 節目/系列/集）
        series = find_series(t_rel)
        ordmap = dir_order(series)
        k = ordmap.get(t_rel)
        if k is None:
            # 退回：上層節目頁（例 yoyotv/index.html）的條目順序，取「系列」在節目中的位置
            up = os.path.dirname(series)
            upmap = dir_order(up) if up and up != series else {}
            k = upmap.get(series)
            if k is not None:
                k = k * 1000  # 同系列內再按集數
                em = re.search(r'第(\d+)集', t_rel)
                k += int(em.group(1)) if em else 500
        if k is None:
            k = 10 ** 5 + len(keys)  # 找不到 → 保持相對順序排最後
        keys.append((k, li))

    if [k for k, _ in keys] == sorted([k for k, _ in keys]):
        return 0
    ordered = [li for _, li in sorted(keys, key=lambda x: x[0])]
    new_body = body
    # 逐項替換：把 body 內原本 li 序列換成新序列
    new_body = body
    for old, new in zip(items, ordered):
        pass
    # 簡單做法：把 body 中所有 li 依序清掉，再重塞（保留 li 之間的空白字元樣式）
    sep = ''
    m_sep = re.search(r'</li>(\s*)<li', body)
    if m_sep:
        sep = m_sep.group(1)
    first = body.find(items[0])
    head_extra = body[:first] if first > 0 else ''
    tail_extra = body[body.rfind(items[-1]) + len(items[-1]):] if items else ''
    new_body = head_extra + sep.join(ordered) + tail_extra
    new_h = h[:m.start()] + m.group(1) + new_body + m.group(3) + h[m.end():]
    if not DRY:
        open(path, 'w', encoding='utf-8').write(new_h)
    return 1


if ONLY:
    files = [ONLY]
else:
    files = []
    for dp, _, fs in os.walk(ROOT):
        if 'index.html' in fs:
            files.append(os.path.join(dp, 'index.html'))

n = 0
for f in files:
    n += fix_page(f)
print(f'{"[DRY] " if DRY else ""}重排 {n} 頁')
