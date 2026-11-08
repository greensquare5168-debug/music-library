#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOYO嘻遊記：第15季 12 集名稱加上空格（地點/主題之間），並修正賽季排序（第08季跑到最後）。
同步更新：列表 rn、頁面 h1/title、麵包屑、tree.json、search-index.json。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOW = ROOT / '罐頭音樂研究所' / 'yoyotv' / 'yoyo嘻遊記'

PAIRS = [
    ('台中神攝手美照帶著走', '台中神攝手 美照帶著走'),
    ('南投出任務奶爸大挑戰', '南投出任務 奶爸大挑戰'),
    ('探索趣味屏東多方way', '探索趣味 屏東多方way'),
    ('新竹小駕駛夢想駕訓班', '新竹小駕駛 夢想駕訓班'),
    ('人小志氣高實現英雄夢', '人小志氣高 實現英雄夢'),
    ('雲林築夢趣小店長培訓班', '雲林築夢趣 小店長培訓班'),
    ('宜蘭上課趣知識樂無窮', '宜蘭上課趣 知識樂無窮'),
    ('台東私房遊五星行程GO', '台東私房遊 五星行程GO'),
    ('嘻遊到台中交友hen簡單', '嘻遊到台中 交友hen簡單'),
    ('生日特別企劃台北大驚喜', '生日特別企劃 台北大驚喜'),
    ('嘻遊吃飽飽台南美食通', '嘻遊吃飽飽 台南美食通'),
    ('台東輕旅行閨蜜出遊趣', '台東輕旅行 閨蜜出遊趣'),
]
# 麵包屑用的是「【地點】主題！副題！」格式
CRUMB_PAIRS = [
    ('【台中】台中神攝手！美照帶著走！', '台中神攝手 美照帶著走'),
    ('【南投】南投出任務！奶爸大挑戰！', '南投出任務 奶爸大挑戰'),
    ('【屏東】探索趣味！屏東多方way！', '探索趣味 屏東多方way'),
    ('【新竹】新竹小駕駛！夢想駕訓班！', '新竹小駕駛 夢想駕訓班'),
    ('【高雄】人小志氣高！實現英雄夢！', '人小志氣高 實現英雄夢'),
    ('【雲林】雲林築夢趣！小店長培訓班！', '雲林築夢趣 小店長培訓班'),
    ('【宜蘭】宜蘭上課趣！知識樂無窮！', '宜蘭上課趣 知識樂無窮'),
    ('【台東】台東私房遊！五星行程GO！', '台東私房遊 五星行程GO'),
    ('【台中】嘻遊到台中！交友hen簡單！', '嘻遊到台中 交友hen簡單'),
    ('【台北】生日特別企劃！台北大驚喜！', '生日特別企劃 台北大驚喜'),
    ('【台南】嘻遊吃飽飽！台南美食通！', '嘻遊吃飽飽 台南美食通'),
    ('【台東】台東輕旅行！閨蜜出遊趣！', '台東輕旅行 閨蜜出遊趣'),
]

def replace_all():
    n = 0
    for f in ROOT.rglob('index.html'):
        try:
            h = f.read_text(encoding='utf-8')
        except Exception:
            continue
        o = h
        for a, b in CRUMB_PAIRS:
            h = h.replace(a, b)
        for a, b in PAIRS:
            h = h.replace(a, b)
        if h != o:
            f.write_text(h, encoding='utf-8')
            n += 1
    print('html files updated:', n)
    # tree.json / search-index.json
    for name in ('tree.json', 'search-index.json'):
        p = ROOT / name
        s = p.read_text(encoding='utf-8')
        o = s
        for a, b in CRUMB_PAIRS + PAIRS:
            s = s.replace(json.dumps(a, ensure_ascii=False)[1:-1], json.dumps(b, ensure_ascii=False)[1:-1])
        if s != o:
            p.write_text(s, encoding='utf-8')
            print(name, 'updated')

def reorder_seasons():
    p = SHOW / 'index.html'
    h = p.read_text(encoding='utf-8')
    m = re.search(r'(<ul class="albumlist">)(.*?)(</ul>)', h, re.S)
    if not m:
        print('albumlist not found')
        return
    items = re.findall(r'<li>.*?</li>', m.group(2), re.S)
    def key(it):
        mm = re.search(r'第(\d+)季', it)
        return int(mm.group(1)) if mm else 999
    items.sort(key=key)
    h = h[:m.start(2)] + ''.join(items) + h[m.end(2):]
    p.write_text(h, encoding='utf-8')
    print('seasons reordered:', len(items))

if __name__ == '__main__':
    replace_all()
    reorder_seasons()
