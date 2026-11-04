#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 MFP《MFPL-20 Best of Film Scores》(100 首) 建進「圖書館音樂研究所」正式網站。

- 新增 label 頁：罐頭音樂研究所/圖書館音樂/music-for-productions/
- 新增專輯頁：.../mfpl-20-best-of-film-scores/
- 新增 100 個曲目頁：.../<slug>/
- 更新 tree.json（左欄導覽）與 search-index.json（站內搜尋）

資料來源：data/mfpl20.json（由 MFP / SourceAudio 曲庫抓取）
"""
import json
import re
import sys
import html
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent          # 網站demo2/
LIB = '罐頭音樂研究所/圖書館音樂'
SITE_PREFIX = '/music-library/'
LABEL_SLUG = 'music-for-productions'
LABEL_NAME = 'Music For Productions'
ALBUM_SLUG = 'mfpl-20-best-of-film-scores'
ALBUM_CODE = 'MFPL-20'
ALBUM_TITLE = 'Best of Film Scores'
CSS_VER = '20261104c'
JS_VER = '20261104e'

abs_url = lambda *parts: SITE_PREFIX + '/'.join(quote(p) for p in parts) + '/'


def esc(s):
    return html.escape(s or '', quote=True)


def slugify(s):
    s = (s or '').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')


# ── 模板零件 ────────────────────────────────────────────────
def head(title, depth):
    up = '../' * depth
    return f'''<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}｜圖書館音樂研究所</title>
<link rel="stylesheet" href="{up}style.css?v={CSS_VER}">
</head><body data-show="{LABEL_SLUG}">
<header class="site-head"><div class="wrap head-row">
  <div><a class="brand" href="{up}index.html">圖書館音樂研究所</a></div>
  <nav class="topnav">
    <a class="navbtn" href="{up}罐頭音樂研究所/圖書館音樂/index.html">音樂圖書館</a>
    <a class="navbtn" href="{up}使用公司/index.html">使用公司</a>
  <span class="navsearch"><input class="navq" type="search" data-go="{up}搜尋/index.html" placeholder="搜尋…" style="font:inherit;font-size:13px;padding:5px 9px;border:1px solid #cfd8e3;border-radius:8px;width:150px"><button class="navgo" type="button" style="font:inherit;font-size:13px;padding:5px 10px;border-radius:8px;border:1px solid #2f6feb;background:#2f6feb;color:#fff;cursor:pointer">搜尋</button></span></nav>
</div></header>
'''


def foot(depth):
    up = '../' * depth
    return f'''<footer class="wrap muted">資料來源：Point Music／Production Music Wiki／Discogs／Music For Productions（SourceAudio）　· 由 U4 整理生成（本全名＋使用頁面）</footer>
<script src="{up}app.js?v={JS_VER}"></script>
</body></html>
'''


def crumb(items, depth):
    """items: [(text, href_abs_or_None)]；href 一律絕對路徑 /music-library/..."""
    out = []
    for text, href in items:
        if href:
            out.append(f'<a href="{href}">{esc(text)}</a>')
        else:
            out.append(esc(text))
    return '<div class="crumb">' + ' / '.join(out) + '</div>'


def label_tree_ul():
    """左欄：label 清單（沿用既有頁面的清單，改成絕對路徑並插入 MFP）。"""
    src = (ROOT / LIB / 'mode-production-music' / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<ul class="tree">.*?</ul>', src, re.S)
    ul = m.group(0)
    # href 全部改絕對
    def fix(mm):
        slug = mm.group(1).rstrip('/')
        return f'href="{abs_url(LIB, slug)}"'
    ul = re.sub(r'href="[^"]*?/([^"/]+)/"', fix, ul)
    # 在 Mode 之後插入 MFP
    li_mfp = f'<li><a href="{abs_url(LIB, LABEL_SLUG)}">{LABEL_NAME}</a></li>'
    marker = re.search(r'<li><a href="' + re.escape(abs_url(LIB, 'mode-production-music')) + r'">Mode</a></li>', ul)
    if marker:
        ul = ul[:marker.end()] + li_mfp + ul[marker.end():]
    else:
        ul = ul.replace('</ul>', li_mfp + '</ul>')
    return ul


def album_tree_ul(tracks):
    items = ''.join(
        f'<li><a href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG, t["slug"])}">{esc(t["label_name"])}</a></li>'
        for t in tracks)
    return f'<div class="tree-h">{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</div><ul class="tree">{items}</ul>'


def aside(depth, tracks, cur_slug=None, with_tracks=True):
    label_ul = label_tree_ul()
    first = (f'<div class="tree-h"><a href="{abs_url(LIB)}">音樂圖書館</a></div>{label_ul}'
             f'<div class="tree-h">{LABEL_NAME}</div><ul class="tree">'
             f'<li><a href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG)}">{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</a></li></ul>')
    if with_tracks:
        first += album_tree_ul(tracks)
    return f'<aside class="treebox">{first}</aside>'


# ── 主資料 ──────────────────────────────────────────────────
def load_tracks():
    cand = [ROOT.parent / '網站demo' / 'data' / 'mfpl20.json',
            Path('/home/jasonlin/clawd/projects/罐頭音樂/網站demo/data/mfpl20.json')]
    src = next((c for c in cand if c.exists()), None)
    if src is None:
        sys.exit('找不到 mfpl20.json')
    data = json.loads(src.read_text(encoding='utf-8'))
    tr = data['labels'][0]['albums'][0]['tracks']
    out = []
    for t in tr:
        composer = t.get('composer') or ''
        label_name = f"{t['title']} - {composer}" if composer else t['title']
        out.append({
            'no': t.get('no', ''),
            'title': t['title'],
            'composer': composer,
            'desc': t.get('desc', ''),
            'genre': t.get('genre', ''),
            'keywords': t.get('keywords', ''),
            'lib': t.get('lib', ''),
            'label_name': label_name,
            'slug': slugify(label_name),
        })
    return out


def build_pages(tracks):
    libdir = ROOT / LIB
    # 1) label 頁
    d = libdir / LABEL_SLUG
    d.mkdir(parents=True, exist_ok=True)
    rows = ''.join(
        f'<li><a class="row" href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG)}">'
        f'<span class="rn">{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</span><span class="muted"></span>'
        f'<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>'
        f'<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;line-height:1;transform:translateY(0.5px)">›</span></a></li>'
        for _ in [0])
    content = (f'<div class="content"><div class="album-card"><h1>{esc(LABEL_NAME)}</h1>'
               f'<div class="album-meta"><span class="pill">1 張專輯</span>'
               f'<span class="pill">100 首曲目</span></div>'
               f'<ul class="albumlist">{rows}</ul></div></div>')
    (d / 'index.html').write_text(
        head(LABEL_NAME, 3)
        + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, None)], 3)}'
        + f'<div class="layout">{aside(3, tracks, with_tracks=False)}'
        + content + '</div></main>' + foot(3), encoding='utf-8')

    # 2) 專輯頁
    d = libdir / LABEL_SLUG / ALBUM_SLUG
    d.mkdir(parents=True, exist_ok=True)
    rows = ''.join(
        f'<li><a class="row" href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG, t["slug"])}">'
        f'<span class="rn">{esc(t["label_name"])}</span><span class="muted"></span>'
        f'<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>'
        f'<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;line-height:1;transform:translateY(0.5px)">›</span></a></li>'
        for t in tracks)
    content = (f'<div class="content"><div class="album-card"><h1>{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</h1>'
               f'<div class="album-meta">'
               f'<span class="pill">Music For Productions – Library</span><span class="pill">2016</span>'
               f'<span class="pill">100 首（合輯，2016-06-22 發行）</span>'
               f'<a class="pill linkpill" href="https://search.musicforproductions.com/album/524836" target="_blank" rel="noopener">音樂庫頁 ↗</a></div>'
               f'<div class="album-desc">Cinematic orchestral soundtracks from experienced MFP composers.</div>'
               f'<ul class="albumlist">{rows}</ul></div></div>')
    (d / 'index.html').write_text(
        head(f'{ALBUM_CODE} - {ALBUM_TITLE}', 4)
        + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, abs_url(LIB, LABEL_SLUG)), (f"{ALBUM_CODE} - {ALBUM_TITLE}", None)], 4)}'
        + f'<div class="layout">{aside(4, tracks)}' + content + '</div></main>' + foot(4), encoding='utf-8')

    # 3) 曲目頁 ×100
    for t in tracks:
        d = libdir / LABEL_SLUG / ALBUM_SLUG / t['slug']
        d.mkdir(parents=True, exist_ok=True)
        meta = []
        if t['desc']:
            meta.append(f'<div class="muted" style="margin:4px 0 10px">{esc(t["desc"])}</div>')
        info = []
        if t['genre']:
            info.append(f'<div class="muted">類型：{esc(t["genre"])}</div>')
        if t['keywords']:
            info.append(f'<div class="muted">關鍵字：{esc(t["keywords"])}</div>')
        alias = ('<div class="muted" style="margin-top:8px">※ Tracks &amp; Fields 平台以別名 '
                 '<b>Creeping Around</b> 上架（同曲）</div>') if t['title'] == 'Tiptoes' else ''
        src = (f'<ul class="entries"><li><a href="{esc(t["lib"])}" target="_blank" rel="noopener">'
               f'Music For Productions 曲目頁 ↗</a></li></ul>') if t['lib'] else ''
        content = (f'<div class="content"><div class="album-card"><h1>{esc(t["label_name"])}</h1>'
                   + ''.join(meta) + ''.join(info)
                   + '<ul class="entries"><li><span class="muted">站上尚未發現使用</span></li></ul>'
                   + src + alias + '</div></div>')
        (d / 'index.html').write_text(
            head(t['label_name'], 5)
            + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, abs_url(LIB, LABEL_SLUG)), (f"{ALBUM_CODE} - {ALBUM_TITLE}", abs_url(LIB, LABEL_SLUG, ALBUM_SLUG)), (t["label_name"], None)], 5)}'
            + f'<div class="layout">{aside(5, tracks, cur_slug=t["slug"])}' + content + '</div></main>' + foot(5),
            encoding='utf-8')


def update_tree(tracks):
    p = ROOT / 'tree.json'
    tree = json.loads(p.read_text(encoding='utf-8'))

    lib = None
    stack = list(tree)
    while stack and lib is None:
        n = stack.pop()
        if n.get('n') == '音樂圖書館':
            lib = n
            break
        stack.extend(n.get('c', []))
    if lib is None:
        sys.exit('tree.json 找不到 音樂圖書館 節點')

    node = {
        'n': LABEL_NAME,
        'h': f'{LIB}/{LABEL_SLUG}/',
        'c': [{
            'n': f'{ALBUM_CODE} - {ALBUM_TITLE}',
            'h': f'{LIB}/{LABEL_SLUG}/{ALBUM_SLUG}/',
            'c': [{'n': t['label_name'], 'h': f'{LIB}/{LABEL_SLUG}/{ALBUM_SLUG}/{t["slug"]}/'} for t in tracks],
        }],
    }
    kids = lib.setdefault('c', [])
    kids[:] = [k for k in kids if k.get('n') != LABEL_NAME]
    # 依名稱字母序插入（Mode 之後 / Music House 之前）
    pos = len(kids)
    for i, k in enumerate(kids):
        if (k.get('n') or '').lower() > LABEL_NAME.lower():
            pos = i
            break
    kids.insert(pos, node)
    p.write_text(json.dumps(tree, ensure_ascii=False), encoding='utf-8')
    print(f'tree.json: labels={len(kids)} (inserted at {pos})')


def update_search(tracks):
    p = ROOT / 'search-index.json'
    idx = json.loads(p.read_text(encoding='utf-8'))
    enc = lambda *parts: '../' + '/'.join(quote(x) for x in parts) + '/'
    idx = [x for x in idx if LABEL_SLUG not in x.get('p', '')]

    track_k = '|'.join(f'{t["label_name"]}✕›' for t in tracks)
    idx.append({'t': LABEL_NAME, 'p': enc(LIB, LABEL_SLUG), 'k': f'{ALBUM_CODE} - {ALBUM_TITLE}✕›'})
    idx.append({'t': f'{ALBUM_CODE} - {ALBUM_TITLE}', 'p': enc(LIB, LABEL_SLUG, ALBUM_SLUG), 'k': track_k})
    for t in tracks:
        idx.append({'t': t['label_name'], 'p': enc(LIB, LABEL_SLUG, ALBUM_SLUG, t['slug'])})
    p.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
    print(f'search-index.json: {len(idx)} entries (+{2 + len(tracks)})')


if __name__ == '__main__':
    tracks = load_tracks()
    print('tracks', len(tracks), 'e.g.', tracks[0]['label_name'], '→', tracks[0]['slug'])
    build_pages(tracks)
    update_tree(tracks)
    update_search(tracks)
    print('done')
