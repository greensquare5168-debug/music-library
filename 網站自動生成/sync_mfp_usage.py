#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自動同步 MFP 曲目的「使用頁面」：掃全站頁面裡指向 MFP 曲目頁的連結。

做法：
1. 走訪站上所有 index.html，找 href 含 search.musicforproductions.com/track/<id>
2. 以該頁 h1（沒有就用 title）當頁面名稱，路徑轉成 /music-library/... 絕對網址
3. 把 <id> → [頁面] 對應寫回 MFPL*_data_*.json 的 tracks[].pages（與手動記錄合併、去重）
之後跑 build_mfp_albums.py 重建頁面即可。
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT.parent / '圖書館音樂研究所'
TRACK_RE = re.compile(r'https://search\.musicforproductions\.com/track/(\d+)')


def page_path(f: Path) -> str:
    rel = f.parent.relative_to(ROOT)
    return '/music-library/' + '/'.join(quote(p) for p in rel.parts) + '/'


def page_name(s: str, f: Path) -> str:
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if t:
            return t
    m = re.search(r'<title>(.*?)</title>', s, re.S)
    return (m.group(1).split('｜')[0].strip() if m else f.parent.name)


def main():
    usage = {}      # track id -> {page_path: name}
    files = [f for f in ROOT.rglob('index.html')]
    scanned = 0
    for f in files:
        try:
            s = f.read_text(encoding='utf-8')
        except Exception:
            continue
        ids = TRACK_RE.findall(s)
        if not ids:
            continue
        # 排除曲目頁本身（它自己也會連到 MFP 曲目頁）
        if '/music-for-productions/' in str(f):
            continue
        scanned += 1
        name = page_name(s, f)
        path = page_path(f)
        for tid in set(ids):
            usage.setdefault(tid, {})[path] = name
    print(f'掃描 {len(files)} 頁，其中 {scanned} 頁含 MFP 曲目連結；命中曲目 {len(usage)} 首')

    total_new = 0
    for jf in sorted(DATA_DIR.glob('MFPL*_data_*.json')):
        d = json.loads(jf.read_text(encoding='utf-8'))
        tracks = d['labels'][0]['albums'][0]['tracks']
        changed = 0
        for t in tracks:
            m = TRACK_RE.search(t.get('lib', ''))
            if not m:
                continue
            tid = m.group(1)
            cur = {p['url']: p['name'] for p in t.get('pages', [])}
            for path, name in usage.get(tid, {}).items():
                if path not in cur:
                    cur[path] = name
                    changed += 1
            t['pages'] = [{'name': n, 'url': u} for u, n in sorted(cur.items())]
        if changed:
            jf.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
        total_new += changed
        print(f'  {jf.name}: +{changed} 筆使用紀錄')
    print('合計新增', total_new)


if __name__ == '__main__':
    main()
