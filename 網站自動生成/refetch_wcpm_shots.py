#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重拍 WCPM（warnerchappellpm.com）來源截圖：用 thum.io 以 1536 寬截圖，
再裁成 1536x695（瀏覽器可視範圍），存回 assets/srcimg/<原名>.jpg。
用法：python3 refetch_wcpm_shots.py [數量]
"""
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'assets' / 'srcimg'
MAP = Path('/tmp/din/wc_map.json')
TARGET_H = 695
WIDTH = 1536

def fetch(url: str) -> bytes:
    api = f'https://image.thum.io/get/width/{WIDTH}/noanimate/{url}'
    req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def process(name: str, url: str) -> str:
    raw = fetch(url)
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    if im.size[0] < 1000:          # 佔位圖（尚未產生）
        return 'placeholder'
    w, h = im.size
    if h > TARGET_H:
        im = im.crop((0, 0, w, TARGET_H))
    out = IMG / name
    im.save(out.with_suffix('.jpg'), quality=86, optimize=True)
    return f'ok {im.size}'

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    m = json.loads(MAP.read_text(encoding='utf-8'))
    done = 0
    for name, url in list(m.items()):
        if done >= limit:
            break
        try:
            r = process(name, url)
        except Exception as e:
            r = f'fail {type(e).__name__}'
        print(name, r, flush=True)
        if r.startswith('ok'):
            done += 1
        time.sleep(1.5)

if __name__ == '__main__':
    main()
