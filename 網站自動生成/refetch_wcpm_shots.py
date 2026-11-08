#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重拍 WCPM 來源截圖（thum.io，1200 寬）並統一裁成 1200x695（= 本站內嵌視窗高度）。
- 輸入：/tmp/din/wc_map.json（檔名 -> WCPM 曲目網址）
- 狀態：/tmp/din/wc_done.txt（已完成檔名，可續跑）
- log ：/tmp/din/wc_refetch.log
用法：python3 refetch_wcpm_shots.py [worker_id] [workers]
"""
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'assets' / 'srcimg'
MAP = Path('/tmp/din/wc_map.json')
DONE = Path('/tmp/din/wc_done.txt')
LOG = Path('/tmp/din/wc_refetch.log')
WIDTH, HEIGHT = 1200, 695

def log(msg):
    with LOG.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')

def fetch(url):
    api = f'https://image.thum.io/get/width/{WIDTH}/noanimate/{url}'
    req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=150) as r:
        return r.read()

def main():
    wid = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    m = json.loads(MAP.read_text(encoding='utf-8'))
    items = [kv for i, kv in enumerate(sorted(m.items())) if i % workers == wid]
    while True:
        pending = [kv for kv in items if not (DONE.exists() and kv[0] in DONE.read_text(encoding='utf-8').split())]
        if not pending:
            log(f'[w{wid}] all done ({len(items)})')
            return
        name, url = pending[0]
        try:
            raw = fetch(url)
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            if im.size[0] < 900:
                raise ValueError(f'placeholder {im.size}')
            im = im.crop((0, 0, im.size[0], min(HEIGHT, im.size[1])))
            if im.size[1] < HEIGHT:
                raise ValueError(f'short {im.size}')
            im.save(IMG / name, quality=86, optimize=True)
            with DONE.open('a', encoding='utf-8') as f:
                f.write(name + '\n')
            log(f'[w{wid}] ok {name} {im.size}')
        except Exception as e:
            log(f'[w{wid}] fail {name} {type(e).__name__} {e}')
            time.sleep(5)
        time.sleep(1.0)

if __name__ == '__main__':
    main()
