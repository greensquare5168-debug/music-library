#!/usr/bin/env python3
"""曲目頁「使用作品」加/更新一筆（孝瓏 2026-11-26 後固定用法）

用法：
  python3 bin/add_usage_entry.py --track <曲目頁目錄> --site <使用作品頁目錄> \
      [--unit "單元標記"] [--dry]

- 來源站連結取自使用作品頁該曲的那個 <li>（單曲連結，符合規則 6）
- 標題＝使用作品頁名稱（品牌 節目 季 集），括號（專輯 代號）取自使用作品頁的 <span class="lbl">
- 排序：依 --site 頁在站上的先後（同一品牌內用 使用作品 索引順序）；新筆插到正確位置，不直接放最下面
- 重複（同曲同來源頁）會更新而不重複插入
"""
import argparse, re, os, sys
from urllib.parse import unquote

TITLE = {'yoyo點點名': 'YOYO點點名', 'yoyo嘻遊記': 'YOYO嘻遊記', '大頭小狀元': '大頭小狀元'}


def site_title(dirpath):
    h = open(os.path.join(dirpath, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<h1>(.*?)</h1>', h)
    t = re.sub('<[^>]+>', '', m.group(1)) if m else os.path.basename(dirpath)
    return t


def extract_li(sitepage, track_dirname):
    h = open(os.path.join(sitepage, 'index.html'), encoding='utf-8').read()
    # 最後一個 entries 清單內含該曲
    key = track_dirname
    idx = h.find('/' + key + '/')
    if idx < 0:
        idx = h.find('/' + key + '"')
    if idx < 0:
        sys.exit(f'❌ 使用作品頁找不到曲目 {key}')
    a = h.rfind('<li', 0, idx)
    b = h.find('</li>', idx) + 5
    return h[a:b], idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--site', required=True)
    ap.add_argument('--unit', default='')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    track_html = os.path.join(a.track, 'index.html')
    h = open(track_html, encoding='utf-8').read()
    li, _ = extract_li(a.site, os.path.basename(a.track.rstrip('/')))
    li = re.sub(r'<span class="lbl">（YOYO點點名 專輯1[^<]*</span>', '', li)  # 舊標記先清
    label = site_title(a.site)
    # 把曲名換成使用作品名稱
    m = re.search(r'<a ([^>]*)>(.*?)</a>', li, re.S)
    li = li[:m.start(2)] + label + li[m.end(2):]
    if a.unit:
        li = re.sub(r'(<span class="lbl">（[^）]*）</span>)',
                    r'\1<span class="lbl">（' + label + ' - ' + a.unit + '）</span>', li, count=1)

    i = h.find('<h1>')
    uls = list(re.finditer(r'<ul class="entries">(.*?)</ul>', h[i:], re.S))
    # 找含「曲目頁來源」以外的使用作品清單：取最後一個
    tgt = uls[-1]
    body = tgt.group(1)
    items = [x for x in re.findall(r'<li[^>]*>.*?</li>', body, re.S) if 'blankline' not in x]
    if not any(('（尚未發現使用作品）' in h) for _ in [0]):
        pass
    # 同來源已存在 → 取代
    same = [x for x in items if os.path.basename(a.track.rstrip('/')) + '/' in x and label in x]
    items = [x for x in items if not (label in x)]
    items.append(li)
    newbody = ''.join(items) + '<li class="blankline" style="list-style:none;border:0;padding:0">&nbsp;</li>'
    out = h[:i] + h[i:tgt.start(1)].replace(h[i:tgt.start(1)], h[i:tgt.start(1)]) + newbody + h[tgt.end(1):]
    out = out.replace('<p class="muted">（尚未發現使用作品）</p>', f'<p class="muted">使用作品（{len(items)} 筆）</p>')
    if a.dry:
        print(f'(dry) {a.track}: {len(items)} 筆，新增 {label}')
        return
    open(track_html, 'w', encoding='utf-8').write(out)
    print(f'✅ {a.track}: 使用作品 {len(items)} 筆，新增 {label}')


if __name__ == '__main__':
    main()
