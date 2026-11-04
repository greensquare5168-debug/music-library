#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 MFP《MFPL-20 Best of Film Scores》建進「圖書館音樂研究所」正式網站（v2）。

v2 調整（孝瓏 2026-11-04）：
- 不做 100 個曲目頁（曲目只在專輯頁列出，點擊外連 MFP 原站）
- 廠牌頁與專輯頁都加「全部／已使用」篩選（與站上其他廠牌頁一致）
- 音樂圖書館首頁（index.html）的廠牌清單要出現 Music For Productions
- tree.json 只放 廠牌→專輯；search-index 只加 廠牌＋專輯

資料來源：圖書館音樂研究所/MFPL20_data_20261104.json（由 MFP / SourceAudio album 524836 抓取）
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


def rel_url(depth, *parts):
    return ('../' * depth) + '/'.join(quote(p) for p in parts) + '/'


FILTER_CSS = '''<style>
.albumfilter{display:flex;gap:8px;align-items:center;margin:6px 0 12px;flex-wrap:wrap}
.albumfilter .afbtn{font:inherit;font-size:14px;padding:5px 12px;border-radius:999px;border:1px solid #cfd8e3;background:#fff;color:#334;cursor:pointer}
.albumfilter .afbtn.active{background:#2f6feb;border-color:#2f6feb;color:#fff}
.albumfilter .afstat{margin-left:auto;font-size:13px;color:#6b7280}
</style>'''

FILTER_JS_TMPL = '''<script>
(function(){
 var bar=document.querySelector('.albumfilter'); if(!bar) return;
 var ul=document.querySelector('ul.albumlist'); if(!ul) return;
 var rows=[].slice.call(ul.querySelectorAll('li'));
 function used(r){return !r.querySelector('.mark-x');}
 var n=rows.filter(used).length, stat=bar.querySelector('.afstat');
 if(stat){stat.textContent='已使用 '+n+' / '+rows.length+' __UNIT__';}
 var key='af:'+location.pathname;
 function apply(f){
  rows.forEach(function(r){r.style.display=(f==='used'&&!used(r))?'none':'';});
  [].forEach.call(bar.querySelectorAll('.afbtn'),function(b){b.classList.toggle('active',b.getAttribute('data-f')===f);});
  try{localStorage.setItem(key,f);}catch(e){}
 }
 [].forEach.call(bar.querySelectorAll('.afbtn'),function(b){b.addEventListener('click',function(){apply(b.getAttribute('data-f'));});});
 var f='all'; try{f=localStorage.getItem(key)||'all';}catch(e){}
 apply(f);
})();
</script>'''


def filter_js(unit):
    return FILTER_JS_TMPL.replace('__UNIT__', unit)


def filter_bar():
    return ('<div class="albumfilter">'
            '<button class="afbtn active" data-f="all">全部</button>'
            '<button class="afbtn" data-f="used">已使用</button></div>')


def head(title, depth, with_filter=False):
    up = '../' * depth
    return f'''<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}｜圖書館音樂研究所</title>
<link rel="stylesheet" href="{up}style.css?v={CSS_VER}">
{FILTER_CSS if with_filter else ''}</head><body data-show="{LABEL_SLUG}">
<header class="site-head"><div class="wrap head-row">
  <div><a class="brand" href="{up}index.html">圖書館音樂研究所</a></div>
  <nav class="topnav">
    <a class="navbtn" href="{up}罐頭音樂研究所/圖書館音樂/index.html">音樂圖書館</a>
    <a class="navbtn" href="{up}使用公司/index.html">使用公司</a>
  <span class="navsearch"><input class="navq" type="search" data-go="{up}搜尋/index.html" placeholder="搜尋…" style="font:inherit;font-size:13px;padding:5px 9px;border:1px solid #cfd8e3;border-radius:8px;width:150px"><button class="navgo" type="button" style="font:inherit;font-size:13px;padding:5px 10px;border-radius:8px;border:1px solid #2f6feb;background:#2f6feb;color:#fff;cursor:pointer">搜尋</button></span></nav>
</div></header>
'''


def foot(depth, with_filter=False, unit=''):
    up = '../' * depth
    return (f'<footer class="wrap muted">資料來源：Point Music／Production Music Wiki／Discogs／Music For Productions（SourceAudio）　· 由 U4 整理生成（本全名＋使用頁面）</footer>\n'
            f'<script src="{up}app.js?v={JS_VER}"></script>\n'
            + (filter_js(unit) if with_filter else '') + '\n</body></html>\n')


def crumb(items):
    out = []
    for text, href in items:
        out.append(f'<a href="{href}">{esc(text)}</a>' if href else esc(text))
    return '<div class="crumb">' + ' / '.join(out) + '</div>'


def label_tree_ul():
    src = (ROOT / LIB / 'mode-production-music' / 'index.html').read_text(encoding='utf-8')
    ul = re.search(r'<ul class="tree">.*?</ul>', src, re.S).group(0)

    def fix(mm):
        return f'href="{abs_url(LIB, mm.group(1).rstrip("/"))}"'
    ul = re.sub(r'href="[^"]*?/([^"/]+)/"', fix, ul)
    li_mfp = f'<li><a href="{abs_url(LIB, LABEL_SLUG)}">{LABEL_NAME}</a></li>'
    mode = abs_url(LIB, 'mode-production-music')
    marker = re.search(r'<li><a href="' + re.escape(mode) + r'">Mode</a></li>', ul)
    if marker:
        ul = ul[:marker.end()] + li_mfp + ul[marker.end():]
    else:
        ul = ul.replace('</ul>', li_mfp + '</ul>')
    return ul


def aside(with_album_link=True):
    s = (f'<div class="tree-h"><a href="{abs_url(LIB)}">音樂圖書館</a></div>'
         + label_tree_ul()
         + f'<div class="tree-h">{LABEL_NAME}</div><ul class="tree">'
         f'<li><a href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG)}">{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</a></li></ul>')
    return f'<aside class="treebox">{s}</aside>'


def load_tracks():
    cand = [ROOT.parent / '圖書館音樂研究所' / 'MFPL20_data_20261104.json',
            ROOT.parent / '網站demo' / 'data' / 'mfpl20.json']
    src = next((c for c in cand if c.exists()), None)
    if src is None:
        sys.exit('找不到 MFPL20 資料檔')
    data = json.loads(src.read_text(encoding='utf-8'))
    out = []
    for t in data['labels'][0]['albums'][0]['tracks']:
        composer = t.get('composer') or ''
        out.append({
            'title': t['title'],
            'composer': composer,
            'desc': t.get('desc', ''),
            'genre': t.get('genre', ''),
            'keywords': t.get('keywords', ''),
            'lib': t.get('lib', ''),
            'label_name': f'{t["title"]} - {composer}' if composer else t['title'],
        })
    return out


def mark_x():
    return ('<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;'
            'justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>')


def go():
    return ('<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;'
            'line-height:1;transform:translateY(0.5px)">›</span>')


def build(tracks):
    libdir = ROOT / LIB

    # ── 廠牌頁（標題用官方 logo）──
    d = libdir / LABEL_SLUG
    d.mkdir(parents=True, exist_ok=True)
    row = (f'<li><a class="row" href="{abs_url(LIB, LABEL_SLUG, ALBUM_SLUG)}">'
           f'<span class="rn">{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</span><span class="muted"></span>'
           f'{mark_x()}{go()}</a></li>')
    logo = ('<img src="../../../assets/mfp-logo.png" alt="Music For Productions" '
            'style="display:block;height:46px;width:auto">')
    content = (f'<div class="content"><div class="album-card"><h1>{logo}</h1>'
               f'<div class="album-meta"><span class="pill">1 張專輯</span></div>'
               + filter_bar()
               + f'<ul class="albumlist">{row}</ul></div></div>')
    (d / 'index.html').write_text(
        head(LABEL_NAME, 3, True)
        + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, None)])}'
        + f'<div class="layout">{aside()}' + content + '</div></main>' + foot(3, True, ''),
        encoding='utf-8')

    # ── 專輯頁（同站上其他專輯頁：h1 + 曲目列，不加多餘資訊）──
    d = libdir / LABEL_SLUG / ALBUM_SLUG
    d.mkdir(parents=True, exist_ok=True)
    rows = ''.join(
        f'<li><a class="row" href="{esc(t["lib"])}" target="_blank" rel="noopener">'
        f'<span class="rn">{esc(t["label_name"])}</span><span class="muted"></span>'
        f'{mark_x()}<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;line-height:1;transform:translateY(0.5px)">↗</span></a></li>'
        for t in tracks)
    content = (f'<div class="content"><div class="album-card"><h1>{esc(ALBUM_CODE)} - {esc(ALBUM_TITLE)}</h1>'
               f'<ul class="albumlist">{rows}</ul></div></div>')
    (d / 'index.html').write_text(
        head(f'{ALBUM_CODE} - {ALBUM_TITLE}', 4, False)
        + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, abs_url(LIB, LABEL_SLUG)), (f"{ALBUM_CODE} - {ALBUM_TITLE}", None)])}'
        + f'<div class="layout">{aside()}' + content + '</div></main>' + foot(4, False),
        encoding='utf-8')

    # ── 移除舊的 100 個曲目頁（v1 產物） ──
    removed = 0
    for child in d.iterdir():
        if child.is_dir() and (child / 'index.html').exists():
            for f in child.iterdir():
                f.unlink()
            child.rmdir()
            removed += 1
    print(f'removed {removed} track dirs')


MARK_X = ('<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;'
          'justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>')
GO = ('<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;'
      'line-height:1;transform:translateY(0.5px)">›</span>')


def update_index_html():
    p = ROOT / LIB / 'index.html'
    s = p.read_text(encoding='utf-8')
    changed = False
    # (1) 左欄清單（aside tree）
    if f'/{LABEL_SLUG}/' not in s:
        li = f'<li><a href="../../{quote(LIB)}/{LABEL_SLUG}/">{LABEL_NAME}</a></li>'
        marker = f'<li><a href="../../{quote(LIB)}/music-house/">Music House</a></li>'
        if marker in s:
            s = s.replace(marker, li + marker, 1)
        else:
            s = re.sub(r'(</ul>)', li + r'\1', s, count=1)
        changed = True
    # (2) 主內容的廠牌清單（ul.albumlist）
    if f'href="./{LABEL_SLUG}/"' not in s:
        row = (f'<li><a class="row" href="./{LABEL_SLUG}/"><span class="rn">{esc(LABEL_NAME)}</span>'
               f'<span class="muted"></span>{MARK_X}{GO}</a></li>')
        marker2 = '<li><a class="row" href="./music-house/">'
        if marker2 in s:
            s = s.replace(marker2, row + marker2, 1)
        else:
            print('warning: 主清單找不到 Music House 位置，MFP 未插入主清單')
        changed = True
    if changed:
        p.write_text(s, encoding='utf-8')
        print('index.html: MFP inserted (tree + main list)')
    else:
        print('index.html: already has MFP')


def update_tree():
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
        sys.exit('tree.json 找不到 音樂圖書館')
    node = {'n': LABEL_NAME, 'h': f'{LIB}/{LABEL_SLUG}/',
            'c': [{'n': f'{ALBUM_CODE} - {ALBUM_TITLE}', 'h': f'{LIB}/{LABEL_SLUG}/{ALBUM_SLUG}/'}]}
    kids = lib.setdefault('c', [])
    kids[:] = [k for k in kids if k.get('n') != LABEL_NAME]
    pos = len(kids)
    for i, k in enumerate(kids):
        if (k.get('n') or '').lower() > LABEL_NAME.lower():
            pos = i
            break
    kids.insert(pos, node)
    p.write_text(json.dumps(tree, ensure_ascii=False), encoding='utf-8')
    print(f'tree.json: labels={len(kids)} inserted@{pos} (no track nodes)')


def update_search(tracks):
    p = ROOT / 'search-index.json'
    idx = json.loads(p.read_text(encoding='utf-8'))
    idx = [x for x in idx if LABEL_SLUG not in x.get('p', '')]
    enc = lambda *parts: '../' + '/'.join(quote(x) for x in parts) + '/'
    idx.append({'t': LABEL_NAME, 'p': enc(LIB, LABEL_SLUG), 'k': f'{ALBUM_CODE} - {ALBUM_TITLE}✕›'})
    idx.append({'t': f'{ALBUM_CODE} - {ALBUM_TITLE}', 'p': enc(LIB, LABEL_SLUG, ALBUM_SLUG),
                'k': '|'.join(f'{t["label_name"]}✕↗' for t in tracks)})
    p.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
    print(f'search-index.json: {len(idx)} entries (+2)')


if __name__ == '__main__':
    tracks = load_tracks()
    build(tracks)
    update_index_html()
    update_tree()
    update_search(tracks)
    print('done')
