#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 DL-music 官方站外部連結 404（孝瓏 2026-11-26 20:54「ピエロの帽子 窗口404」）
原因：站方改檔名 JPX-0X_N.html → JPX-vol0X_N.html（1~9 補零、10 以上要注意）
實測：JPX-vol02_1/2/3、JPX-vol05_1 → 200；舊名 404
做法：全站 html 掃 https://dl.music-yamato.jp/JPX-0N_M.html，先 HEAD 驗新網址，
      200 才改；同檔內 JPX-0N_ 出現多次一併換。幂等。
用法： python3 fix_dlmusic_url_scheme_20261126.py [--apply]
"""
import os, re, sys, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv
PAT = re.compile(r'https://dl\.music-yamato\.jp/JPX-(\d{2})_(\d+)\.html')
cache = {}


def ok(url):
    if url not in cache:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-A', 'Mozilla/5.0',
                            '--max-time', '20', url], capture_output=True, text=True)
        cache[url] = r.stdout.strip()
    return cache[url] == '200'


files, changed, skipped = [], 0, {}
for dp, dns, fs in os.walk(BASE):
    dns[:] = [d for d in dns if d not in ('.git', 'node_modules', 'assets')]
    if 'index.html' in fs and 'dl-music' not in dp.split(os.sep):
        pass
    for f in fs:
        if f.endswith('.html'):
            p = os.path.join(dp, f)
            s = open(p, encoding='utf-8').read()
            if PAT.search(s):
                files.append((p, s))

for p, s in files:
    new = s
    for m in set(PAT.finditer(s)):
        old = m.group(0)
        vol, page = m.group(1), m.group(2)
        cand = 'https://dl.music-yamato.jp/JPX-vol%s_%s.html' % (vol, page)
        if ok(cand):
            new = new.replace(old, cand)
        else:
            skipped[old] = skipped.get(old, 0) + 1
    if new != s:
        changed += 1
        if APPLY:
            open(p, 'w', encoding='utf-8').write(new)

print('掃到頁面:', len(files), '| 需修改頁:', changed)
for k, v in skipped.items():
    print('  ! 新網址也不是 200，未改:', k, v)
print('APPLY' if APPLY else 'DRY-RUN')
