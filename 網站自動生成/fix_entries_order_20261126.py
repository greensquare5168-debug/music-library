#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曲目頁「使用作品」排序 v3（2026-11-26 孝瓏定案）

規則：
 1. 第一鍵：作品所屬「節目」目錄（yoyotv/大頭小狀元 這種）—— 取該目錄在品牌頁(`yoyotv/index.html`)的順序
 2. 第二鍵：季／系列目錄在節目 index 頁的順序（大頭小狀元第1/2/3季 → YOYO小狀元第1/2季）
 3. 第三鍵：集在季 index 頁的順序
 4. 找不到精確對應時 → 排該群組最後（不亂插）
 5. 巧連智低年級版 CD：動物大明星那 4 個固定置底

 只動 <ul class="entries"> 內的 <li> 順序，其他一律不動。

用法： python3 fix_entries_order_20261126.py [--dry-run] [--file <path>] [--stats]
"""
import os
import re
import sys
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv
STATS = '--stats' in sys.argv
ONLY = None
if '--file' in sys.argv:
    ONLY = sys.argv[sys.argv.index('--file') + 1]

ENTRIES_RE = re.compile(r'(<ul class="entries">)(.*?)(</ul>)', re.S)
LI_RE = re.compile(r'<li[^>]*>.*?</li>', re.S)
# 品牌（第一層）順序 — 來源：網站「使用公司」選單（tree.json 使用公司節點）
BRAND_ORDER = {
    '公視': 0,
    'yoyotv': 1,
    'momo親子台': 2,
    '巧連智': 3,
    '古古食': 4,
    '圖書館音樂': 5,
}
QLE_BOTTOM = ('哇來看動物大明星', '我是小觀察員', '一起去觀光農場', '博物館大驚奇')

_order_cache = {}


def load_order(rel):
    """讀 rel/index.html 的卡片順序 → {子目錄路徑: 序號}（路徑與傳入 rel 同基準）"""
    rel = rel.rstrip('/')
    if rel in _order_cache:
        return _order_cache[rel]
    order = {}
    idx = os.path.join(rel, 'index.html')
    if os.path.isfile(idx):
        h = open(idx, encoding='utf-8').read()
        hrefs = re.findall(r'<a class="row"[^>]*href="([^"]+)"', h)
        if not hrefs:
            hrefs = re.findall(r'<a href="([^"]+)"[^>]*><span class="rn">', h)
        for n, hf in enumerate(hrefs):
            t = os.path.normpath(os.path.join(rel, urllib.parse.unquote(hf))).rstrip('/')
            if t.endswith('index.html'):
                t = os.path.dirname(t)
            t = t.rstrip('/')
            order.setdefault(os.path.abspath(t), n)
    _order_cache[rel] = order
    return order


def locate(absdir):
    """回傳 (節目序, 季序, 集序) 或 None；absdir＝絕對路徑"""
    t_rel = os.path.relpath(absdir, os.getcwd()).rstrip('/')
    segs = t_rel.split(os.sep)
    if len(segs) < 3:
        return None
    # 節目目錄 = ROOT/<品牌或中層>/<節目>；用「上層 index 有把這目錄列為卡片」判定
    prog = None
    for cut in range(3, len(segs)):   # 由淺到深：取最上層被列為卡片的目錄＝節目
        cand = os.sep.join(segs[:cut])
        if not os.path.isfile(os.path.join(cand, 'index.html')):
            continue
        parent = os.path.dirname(cand)
        if os.path.abspath(cand) in load_order(parent):
            prog = cand
            break
    if prog is None:
        return None
    prog_order = load_order(os.path.dirname(prog))
    k1 = prog_order.get(os.path.abspath(prog), 9999)

    rest = t_rel[len(prog) + 1:]
    prog_map = load_order(prog)
    if not rest:
        return (BRAND_ORDER.get(segs[1], 50), k1, -1, -1)
    first = prog + os.sep + rest.split(os.sep)[0]
    if os.path.abspath(first) in prog_map:
        k2 = prog_map[os.path.abspath(first)]
        s_map = load_order(first)
        _tgt = os.path.abspath(absdir).rstrip('/')
        k3 = s_map.get(_tgt)
        if k3 is None:
            k3 = s_map.get(_tgt.replace(os.sep, '/'))
        if k3 is None:
            slug = os.path.basename(t_rel)
            for kk, vv in s_map.items():
                if os.path.basename(kk) == slug:
                    k3 = vv
                    break
        if k3 is None:
            k3 = 9999
    else:
        # 集直接掛在節目下
        k2 = -1
        k3 = prog_map.get(os.path.abspath(absdir.rstrip('/')), 9999)
    # 品牌層順序（2026-11-26 孝瓏：網站上 YOYOTV 在 MOMO 上面 → 狗狗週記要在最下面）
    brand_key = BRAND_ORDER.get(segs[1], 50)
    if '巧連智低年級版cd' in t_rel and any(s in t_rel for s in QLE_BOTTOM):
        k2 = 99999
        k3 = 99999
    return (brand_key, k1, k2, k3)


def fix_page(path):
    page_rel = os.path.dirname(os.path.relpath(path, os.getcwd()))
    h = open(path, encoding='utf-8').read()
    m = ENTRIES_RE.search(h)
    if not m:
        return 0, (0, 0)
    body = m.group(2)
    items = LI_RE.findall(body)
    if len(items) < 2:
        return 0, (0, 0)

    keys, unknown, total = [], 0, 0
    for i, li in enumerate(items):
        am = re.search(r'<a href="([^"]+)"', li)
        if not am or am.group(1).startswith('http'):
            keys.append((10 ** 6, 0, 0, i))
            continue
        href = am.group(1)
        total += 1
        if href.startswith('/music-library/'):
            target = os.path.join(os.getcwd(), urllib.parse.unquote(href[len('/music-library/'):]).rstrip('/'))
        else:
            target = os.path.normpath(os.path.join(page_rel, urllib.parse.unquote(href))).rstrip('/')
        loc = locate(target)
        if loc is None:
            unknown += 1
            keys.append((10 ** 5, 0, 0, i))
        else:
            keys.append(loc)

    kk = [k for k in keys]
    if kk == sorted(kk):
        return 0, (unknown, total)
    ordered = [li for _, li in sorted(zip(keys, items), key=lambda x: x[0])]
    ms = re.search(r'</li>(\s*)<li', body)
    sep = ms.group(1) if ms else ''
    first = body.find(items[0])
    head = body[:first] if first > 0 else ''
    tail = body[body.rfind(items[-1]) + len(items[-1]):]
    new_body = head + sep.join(ordered) + tail
    if not DRY:
        open(path, 'w', encoding='utf-8').write(
            h[:m.start()] + m.group(1) + new_body + m.group(3) + h[m.end():])
    return 1, (unknown, total)


files = [ONLY] if ONLY else [os.path.join(dp, 'index.html')
                             for dp, _, fs in os.walk(ROOT) if 'index.html' in fs]
n = 0
bad = 0
for f in files:
    ch, (unk, tot) = fix_page(f)
    n += ch
    if unk:
        bad += 1
        if STATS and bad <= 10:
            print(f'  ! 有未定位作品 {unk}/{tot}：{os.path.relpath(f, BASE)[-70:]}')
print(f'{"[DRY] " if DRY else ""}重排 {n} 頁（含未定位作品的頁 {bad}）')
