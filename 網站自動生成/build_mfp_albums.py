#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建「Music For Productions」廠牌底下的所有專輯頁（資料驅動、可重跑）。

資料來源：~/clawd/projects/罐頭音樂/圖書館音樂研究所/MFPL*_data_*.json
  - labels[0].albums[0]：code / title / lib_url / tracks[]
  - tracks[]：no, title, composer, desc, genre, keywords, lib, pages[{name,url}]

產出：
  - 廠牌頁 罐頭音樂研究所/圖書館音樂/music-for-productions/index.html
  - 每張專輯頁 <album-slug>/index.html
  - 每首曲目頁 <album-slug>/<track-slug>/index.html
  - tree.json 的 Music For Productions 節點（廠牌→專輯→曲目）
  - search-index.json（廠牌、專輯、曲目）
站上固定版型：廠牌頁＝h1文字＋pill張數＋全部/已使用＋專輯列；album＝h1＋曲目列；track＝h1＋來源預覽圖＋使用頁面 or（尚未發現使用作品）
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent          # 網站demo2/
DATA_DIR = ROOT.parent / '圖書館音樂研究所'
LIB = '罐頭音樂研究所/圖書館音樂'
SITE_PREFIX = '/music-library/'
LABEL_SLUG = 'music-for-productions'
LABEL_NAME = 'Music For Productions'
CSS_VER = '20261104c'
JS_VER = '20261104e'

abs_url = lambda *parts: SITE_PREFIX + '/'.join(quote(p) for p in parts) + '/'


def esc(s):
    return html.escape(s or '', quote=True)


def slugify(s):
    s = (s or '').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')


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


def filter_js(unit=''):
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


def foot(depth, with_filter=False):
    up = '../' * depth
    return (f'<footer class="wrap muted">資料來源：Point Music／Production Music Wiki／Discogs／Music For Productions（SourceAudio）　· 由 U4 整理生成（本全名＋使用頁面）</footer>\n'
            f'<script src="{up}app.js?v={JS_VER}"></script>\n'
            + (filter_js('') if with_filter else '') + '\n</body></html>\n')


def crumb(items):
    return '<div class="crumb">' + ' / '.join(
        (f'<a href="{href}">{esc(text)}</a>' if href else esc(text)) for text, href in items) + '</div>'


def label_tree_ul():
    src = (ROOT / LIB / 'mode-production-music' / 'index.html').read_text(encoding='utf-8')
    ul = re.search(r'<ul class="tree">.*?</ul>', src, re.S).group(0)
    ul = re.sub(r'href="[^"]*?/([^"/]+)/"', lambda m: f'href="{abs_url(LIB, m.group(1).rstrip("/"))}"', ul)
    li_mfp = f'<li><a href="{abs_url(LIB, LABEL_SLUG)}">{LABEL_NAME}</a></li>'
    mode = abs_url(LIB, 'mode-production-music')
    marker = re.search(r'<li><a href="' + re.escape(mode) + r'">Mode</a></li>', ul)
    if marker:
        ul = ul[:marker.end()] + li_mfp + ul[marker.end():]
    elif LABEL_SLUG not in ul:
        ul = ul.replace('</ul>', li_mfp + '</ul>')
    return ul


def aside(albums):
    items = ''.join(f'<li><a href="{abs_url(LIB, LABEL_SLUG, a["slug"])}">{esc(a["label"])}</a></li>' for a in albums)
    return (f'<aside class="treebox"><div class="tree-h"><a href="{abs_url(LIB)}">音樂圖書館</a></div>'
            + label_tree_ul()
            + f'<div class="tree-h">{LABEL_NAME}</div><ul class="tree">{items}</ul></aside>')


def mark(pages):
    if pages:
        return ('<span class="mark" title="有發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;'
                'width:18px;height:18px;padding:0;line-height:1;font-size:11px;background:#eaf7ef;color:#12894a;'
                'border:1px solid #bfe6cd">✓</span>')
    return ('<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;'
            'justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px">✕</span>')


def go():
    return ('<span class="go" style="display:inline-flex;align-items:center;justify-content:center;height:18px;'
            'line-height:1;transform:translateY(0.5px)">›</span>')


def srcb(depth):
    up = '../' * depth
    return ('<span class="srcb" style="position:relative;display:inline-flex;align-items:center;justify-content:center;'
            'width:43px;height:24px;flex:0 0 43px;margin-left:6px;margin-right:10px">'
            f'<span class="ytbadge ytimg" title="{LABEL_NAME}" style="position:static;margin:0;padding:0;background:none;'
            'border-radius:0;box-shadow:none;min-width:0;display:flex;align-items:center;justify-content:center;line-height:0">'
            f'<img src="{up}assets/mfp-logo.png" alt="{LABEL_NAME}" title="{LABEL_NAME}" '
            'style="display:block;max-width:40px;max-height:24px;width:auto;height:auto"></span></span>')


def load_albums():
    albums = []
    for f in sorted(DATA_DIR.glob('MFPL*_data_*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        a = d['labels'][0]['albums'][0]
        code, title = a['code'], a['title']
        tracks = []
        for t in a['tracks']:
            composer = t.get('composer') or ''
            label = f'{t["title"]} - {composer}' if composer else t['title']
            tracks.append({
                'title': t['title'],
                'composer': composer,
                'label': label,
                'slug': slugify(label),
                'file_slug': slugify(t['title']),
                'desc': t.get('desc', ''),
                'genre': t.get('genre', ''),
                'keywords': t.get('keywords', ''),
                'lib': t.get('lib', ''),
                'pages': t.get('pages', []),
            })
        disp = re.sub(r'^([A-Za-z]+)-(\d+)$', r'\1\2', code)   # MFPL-18 → MFPL18（與站上顯示一致）
        albums.append({'code': code, 'title': title, 'label': f'{disp} - {title}',
                       'slug': slugify(f'{code} {title}'), 'lib_url': a.get('lib_url', ''),
                       'tracks': tracks, 'src': f.name})
    albums.sort(key=lambda a: a['code'])
    return albums


def build_label_page(albums):
    rows = ''.join(
        f'<li><a class="row" href="{abs_url(LIB, LABEL_SLUG, a["slug"])}">'
        f'<span class="rn">{esc(a["label"])}</span><span class="muted"></span>'
        f'{mark(any(t["pages"] for t in a["tracks"]))}{srcb(3)}{go()}</a></li>'
        for a in albums)
    content = (f'<div class="content"><div class="album-card"><h1>{esc(LABEL_NAME)}</h1>'
               f'<div class="album-meta"><span class="pill">{len(albums)} 張專輯</span></div>'
               + filter_bar() + f'<ul class="albumlist">{rows}</ul></div></div>')
    d = ROOT / LIB / LABEL_SLUG
    d.mkdir(parents=True, exist_ok=True)
    (d / 'index.html').write_text(
        head(LABEL_NAME, 3, True)
        + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, None)])}'
        + f'<div class="layout">{aside(albums)}' + content + '</div></main>' + foot(3, True),
        encoding='utf-8')


def build_album_pages(albums):
    for a in albums:
        rows = ''.join(
            f'<li><a class="row" href="{abs_url(LIB, LABEL_SLUG, a["slug"], t["slug"])}">'
            f'<span class="rn">{esc(t["label"])}</span><span class="muted"></span>'
            f'{mark(t["pages"])}{srcb(4)}{go()}</a></li>'
            for t in a['tracks'])
        content = (f'<div class="content"><div class="album-card"><h1>{esc(a["label"])}</h1>'
                   f'<ul class="albumlist">{rows}</ul></div></div>')
        d = ROOT / LIB / LABEL_SLUG / a['slug']
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(
            head(a['label'], 4, False)
            + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, abs_url(LIB, LABEL_SLUG)), (a["label"], None)])}'
            + f'<div class="layout">{aside(albums)}' + content + '</div></main>' + foot(4, False),
            encoding='utf-8')

        # 曲目頁
        for t in a['tracks']:
            shot = f'assets/srcimg/mfp-{t["file_slug"]}.png'
            if t['lib']:
                src = (f'<ul class="entries"><li><a class="srcimg" href="{esc(t["lib"])}" target="_blank" rel="noopener" title="點圖前往來源網站">'
                       f'<img src="../../../../../{quote(shot)}" alt="來源預覽圖（點圖前往網站）" loading="lazy" '
                       'style="display:block;width:100%;max-width:920px;height:auto;border:1px solid #e3ecf3;border-radius:10px;margin:6px auto 26px">'
                       '</a></li></ul>')
            else:
                src = ''
            if t['pages']:
                usage = '<ul class="entries">' + ''.join(
                    f'<li><a href="{esc(p["url"])}">{esc(p["name"])}</a></li>' for p in t['pages']) + '</ul>'
            else:
                usage = '<p class="muted">（尚未發現使用作品）</p>'
            content = (f'<div class="content"><div class="album-card"><h1>{esc(t["label"])}</h1>'
                       + src + usage + '</div></div>')
            d2 = ROOT / LIB / LABEL_SLUG / a['slug'] / t['slug']
            d2.mkdir(parents=True, exist_ok=True)
            (d2 / 'index.html').write_text(
                head(t['label'], 5, False)
                + f'<main class="wrap">{crumb([("音樂圖書館", abs_url(LIB)), (LABEL_NAME, abs_url(LIB, LABEL_SLUG)), (a["label"], abs_url(LIB, LABEL_SLUG, a["slug"])), (t["title"], None)])}'
                + f'<div class="layout">{aside(albums)}' + content + '</div></main>' + foot(5, False),
                encoding='utf-8')


def update_tree(albums):
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
    node = {'n': LABEL_NAME, 'h': f'{LIB}/{LABEL_SLUG}/', 'c': []}
    for a in albums:
        node['c'].append({'n': a['label'], 'h': f'{LIB}/{LABEL_SLUG}/{a["slug"]}/',
                          'c': [{'n': t['label'], 'h': f'{LIB}/{LABEL_SLUG}/{a["slug"]}/{t["slug"]}/'} for t in a['tracks']]})
    kids = lib.setdefault('c', [])
    kids[:] = [k for k in kids if k.get('n') != LABEL_NAME]
    pos = len(kids)
    for i, k in enumerate(kids):
        if (k.get('n') or '').lower() > LABEL_NAME.lower():
            pos = i
            break
    kids.insert(pos, node)
    p.write_text(json.dumps(tree, ensure_ascii=False), encoding='utf-8')
    print(f'tree.json: MFP {len(albums)} 張專輯 / {sum(len(a["tracks"]) for a in albums)} 曲')


def update_search(albums):
    p = ROOT / 'search-index.json'
    idx = json.loads(p.read_text(encoding='utf-8'))
    idx = [x for x in idx if LABEL_SLUG not in x.get('p', '')]
    enc = lambda *parts: '../' + '/'.join(quote(x) for x in parts) + '/'
    idx.append({'t': LABEL_NAME, 'p': enc(LIB, LABEL_SLUG),
                'k': '|'.join((a['label'] + ('✓' if any(t['pages'] for t in a['tracks']) else '✕') + '›') for a in albums)})
    for a in albums:
        idx.append({'t': a['label'], 'p': enc(LIB, LABEL_SLUG, a['slug']),
                    'k': '|'.join(f'{t["label"]}{"✓" if t["pages"] else "✕"}›' for t in a['tracks'])})
        for t in a['tracks']:
            idx.append({'t': t['label'], 'p': enc(LIB, LABEL_SLUG, a['slug'], t['slug'])})
    p.write_text(json.dumps(idx, ensure_ascii=False), encoding='utf-8')
    print(f'search-index.json: {len(idx)} 筆')


if __name__ == '__main__':
    albums = load_albums()
    print('albums:', [(a['code'], len(a['tracks'])) for a in albums])
    build_label_page(albums)
    build_album_pages(albums)
    update_tree(albums)
    update_search(albums)
    print('done')
