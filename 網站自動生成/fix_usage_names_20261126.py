#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""曲目頁／集頁「使用作品」名稱修復（2026-11-26 孝瓏反映）

背景：commit 2e9c0ddb634a5（2026-11-26 15:19）用「href 最後一段資料夾名」當連結文字，
      資料夾名本身不完整（缺節目名／缺子集資訊／只是季名）時，畫面上就變成
      「YOYOTV」「YOYO點點名」「流言追追追」「巧連智 ABC Bubbles」這種殘缺名稱。

正式名稱來源：**該集頁自己的 <title>**（去掉「｜圖書館音樂研究所」）
  → 站上各頁顯示的就是這串，最權威，且所有層級（節目/季/單元/集）都適用。

修正對象：所有「使用作品」清單項（.entries 內、帶 .lbl 或 .same 的 li）。
         純導覽（樹狀、麵包屑、專輯曲目清單）一律不動。

用法：
  python3 fix_usage_names_20261126.py --dry-run    # 只看會改什麼
  python3 fix_usage_names_20261126.py             # 實際寫入
"""
import os
import re
import sys
import urllib.parse
import collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(BASE, '罐頭音樂研究所')
DRY = '--dry-run' in sys.argv
PROGS = [d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))]
PROGSET = set(PROGS)


def read(p):
    try:
        return open(p, encoding='utf-8').read()
    except Exception:
        return None


def esc(s):
    return s.replace('&amp;', '&')


def unesc(s):
    return s.replace('&', '&amp;')


# ---------- 1. 建立 (節目, 目標資料夾) -> 目標頁路徑 ----------
PAGEDIR = {}
for prog in PROGS:
    pdir = os.path.join(ROOT, prog)
    for root, _, fs in os.walk(pdir):
        depth = root[len(pdir):].count(os.sep)
        if 1 <= depth <= 3 and 'index.html' in fs:
            PAGEDIR[(prog, os.path.basename(root))] = root


def locate(u):
    """從 /music-library/罐頭音樂研究所/<節目>/…/<目標>/ 解析出 (節目, 目標資料夾)"""
    parts = u.rstrip('/').split('/')
    for i in range(1, len(parts)):
        if parts[i - 1] in PROGSET:
            return parts[i - 1], parts[i]
    return None, None


# ---------- 2. 站上正式名稱 = 目標頁 <title> ----------
dirnames = {}
for (prog, seg), page_dir in PAGEDIR.items():
    dirs = {d for d in os.listdir(page_dir)
            if os.path.isdir(os.path.join(page_dir, d))
            and os.path.isfile(os.path.join(page_dir, d, 'index.html'))}
    if dirs:
        dirnames[(prog, seg)] = dirs

official = {}
for (prog, seg), page_dir in PAGEDIR.items():
    h = read(os.path.join(page_dir, 'index.html'))
    if not h:
        continue
    mt = re.search(r'<title>(.*?)</title>', h, re.S)
    if not mt:
        continue
    t = re.sub(r'<[^>]+>', '', mt.group(1))
    t = re.split(r'\s*[｜|]\s*', t)[0].strip()
    if not t:
        continue
    # 容器頁（季／單元）→ 名稱還需帶上實際集名，看「使用作品」旁邊的括號標記
    official[(prog, seg)] = (esc(t), bool(dirnames.get((prog, seg))))

print(f'站上正式名稱：{len(official)} 筆')

# ---------- 3. 掃全站修正 ----------
LI_RE = re.compile(
    r'<li[^>]*>(?:(?!</li>).)*?<a href="(/music-library/[^"]*?/)"[^>]*>([^<]{1,200})</a>'
    r'(?:(?!</li>).)*?</li>', re.S)

changed = files = 0
report = collections.Counter()
kept = collections.Counter()
examples = []


def fix_page(h, rel):
    global changed

    def repl(m):
        global changed
        full, href, text = m.group(0), m.group(1), m.group(2)
        if '<span class="lbl">' not in full and 'class="same"' not in full:
            return full
        prog, seg = locate(urllib.parse.unquote(href))
        if not prog or (prog, seg) not in official:
            return full
        name, is_container = official[(prog, seg)]
        cur = esc(text.strip())
        if cur == name:
            return full
        # 容器頁（季／單元）：現名已比 title 長（帶了集名）→ 不要往回縮
        if is_container and len(cur) > len(name):
            return full
        # 安全檢查：只改「明顯殘缺」的（現名是正式名前綴／子字串／反過來）
        key = re.sub(r'[^\w\u4e00-\u9fff]', '', cur).lower()
        nkey = re.sub(r'[^\w\u4e00-\u9fff]', '', name).lower()
        if not (key and nkey and (nkey.startswith(key) or key.startswith(nkey) or key in nkey)):
            kept[(cur, name)] += 1
            return full
        new = full.replace(f'>{text}</a>', f'>{unesc(name)}</a>', 1)
        if new == full:
            return full
        changed += 1
        report[(cur, name)] += 1
        if len(examples) < 15:
            examples.append((rel, cur, name))
        return new

    return LI_RE.sub(repl, h)


for dirpath, _, fs in os.walk(ROOT):
    if 'index.html' not in fs:
        continue
    path = os.path.join(dirpath, 'index.html')
    h = read(path)
    if not h:
        continue
    new = fix_page(h, os.path.relpath(path, BASE))
    if new != h:
        files += 1
        if not DRY:
            open(path, 'w', encoding='utf-8').write(new)

print(f'{"[DRY] " if DRY else ""}修正連結 {changed} 處，涉及 {files} 頁')
for (a, b), n in report.most_common(25):
    print(f'  {n:5d}  {a[:44]}  →  {b[:60]}')
if examples:
    print('--- 範例')
    for e in examples[:8]:
        print('  ', e)
if kept:
    print('--- 未動（現名不是正式名前綴，需人工判斷）')
    for (a, b), n in kept.most_common(15):
        print(f'  {n:5d}  {a[:44]}  vs 正式 {b[:60]}')
