#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 assets/srcimg 內來源截圖的白邊裁掉（保留 4px 呼吸），讓內嵌視窗裡內容滿版。
規則：以「非接近白色」像素計算每列/每欄覆蓋率，覆蓋率 > 0.3% 才視為內容。
可重跑（已裁過的不會再變）。
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'assets' / 'srcimg'
PAD = 4
MIN_FRAC = 0.003

def crop_one(p: Path) -> bool:
    try:
        im = Image.open(p)
        im.load()
    except Exception:
        return False
    mode = im.mode
    rgb = im.convert('RGB')
    a = np.array(rgb)
    nonwhite = (a < 243).any(axis=2)
    h, w = nonwhite.shape
    cols = nonwhite.sum(axis=0)
    rows = nonwhite.sum(axis=1)
    cx = np.where(cols > max(1, int(h * MIN_FRAC)))[0]
    ry = np.where(rows > max(1, int(w * MIN_FRAC)))[0]
    if len(cx) == 0 or len(ry) == 0:
        return False
    x0, x1 = int(cx[0]), int(cx[-1])
    y0, y1 = int(ry[0]), int(ry[-1])
    x0 = max(0, x0 - PAD); y0 = max(0, y0 - PAD)
    x1 = min(w - 1, x1 + PAD); y1 = min(h - 1, y1 + PAD)
    if (x1 - x0) >= w - 6 and (y1 - y0) >= h - 6:
        return False  # 已滿版
    out = im.crop((x0, y0, x1 + 1, y1 + 1))
    if mode != 'RGB':
        out = out.convert(mode) if mode in ('P', 'L', 'RGBA') else out
    kw = {'quality': 88, 'optimize': True} if p.suffix.lower() in ('.jpg', '.jpeg') else {}
    out.save(p, **kw)
    return True

def main():
    files = sorted([f for f in DIR.iterdir() if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    n = 0
    for f in files:
        if crop_one(f):
            n += 1
    print(f'cropped {n} / {len(files)}')

if __name__ == '__main__':
    main()
