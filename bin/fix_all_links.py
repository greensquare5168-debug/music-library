#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站連結總修（2026-11-26 孝瓏同意「開始」）
1) 以 ../ 開頭的連結 → 依頁面實際位置解析成 /music-library/<repo 相對路徑>，
   解析不到就往前少算 1~3 層（修層數多算），最後再試目錄改名對照表。
2) 已知改名：on-jiten-2-jingle-bridge → on-jiten-vol2-jingle-bridge
3) 站內 <a href="..."> 的 index.html 尾巴保留；?query / #hash 保留
用法：--apply
"""
import os, re, sys, glob, urllib.parse, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = '--apply' in sys.argv
ATTR = re.compile(r'((?:href|src)=")([^"]+)(")')

# 目錄改名對照（舊名 → 新名）
RENAME = {
    'on-jiten-2-jingle-bridge': 'on-jiten-vol2-jingle-bridge',
}

stats = {'css_dup': 0, 'fixed': 0, 'rename': 0, 'unresolved': 0}
unresolved = {}

def path_ok(relp):
    t = os.path.join(BASE, relp)
    if t.endswith('/') or not os.path.splitext(t)[1]:
        t = os.path.join(t, 'index.html')
    return os.path.isfile(t)

def resolve(page_dir, href):
    """回傳可用的 repo 相對路徑或 None"""
    core = href.split('?')[0].split('#')[0]
    tail = href[len(core):]
    h = urllib.parse.unquote(core)
    rest0 = h
    while rest0.startswith('../'):
        rest0 = rest0[3:]
    up0 = h.count('../')
    trials = []
    for delta in (0, -1, -2, -3, 1, 2):
        up = up0 + delta
        if up < 0:
            continue
        d = page_dir
        for _ in range(up):
            d = os.path.dirname(d)
        trials.append(os.path.normpath(os.path.join(d, rest0)))
    for c in trials:
        relp = os.path.relpath(c, BASE)
        if path_ok(relp):
            return relp, tail
    # 目錄改名再試
    for old, new in RENAME.items():
        if old in h:
            h2 = h.replace(old, new)
            rest2 = h2
            while rest2.startswith('../'):
                rest2 = rest2[3:]
            up2 = h2.count('../')
            d = page_dir
            for _ in range(up2):
                d = os.path.dirname(d)
            c = os.path.normpath(os.path.join(d, rest2))
            relp = os.path.relpath(c, BASE)
            if path_ok(relp):
                return relp, tail
    return None, tail

for p in glob.glob(os.path.join(BASE, '**', 'index.html'), recursive=True):
    rel = os.path.relpath(p, BASE)
    if rel.split(os.sep)[0] in ('bin', '網站自動生成', '.git'):
        continue
    s = open(p, encoding='utf-8', errors='ignore').read()
    page_dir = os.path.dirname(p)
    dirty = [False]

    def sub(m):
        href = m.group(2)
        if href.startswith(('http', 'mailto', '#', 'data:', 'javascript:')):
            return m.group(0)
        # 樣式表重複層數（../../style-...css 或 ../../../style.css）
        if re.search(r'(^|/)style(-[0-9]+)?\.css', href.split('?')[0]):
            newrel, tail = resolve(page_dir, href) if href.startswith('../') else (None, '')
            if newrel and '/music-library/' not in href:
                dirty[0] = True
                stats['css_dup'] += 1
                return m.group(1) + '/music-library/' + urllib.parse.quote(newrel).replace('%2F', '/') + tail + m.group(3)
            return m.group(0)
        if not href.startswith('../'):
            # 站內的 ./xxx/ 或 裸相對路徑且有改名需求
            if any(o in href for o in RENAME):
                newrel, tail = resolve(page_dir, href)
                if newrel:
                    dirty[0] = True
                    stats['rename'] += 1
                    return m.group(1) + '/music-library/' + urllib.parse.quote(newrel).replace('%2F', '/') + tail + m.group(3)
            return m.group(0)
        org = os.path.normpath(os.path.join(page_dir, urllib.parse.unquote(href.split('?')[0].split('#')[0])))
        if path_ok(os.path.relpath(org, BASE)):
            return m.group(0)  # 本來就對
        newrel, tail = resolve(page_dir, href)
        if newrel:
            dirty[0] = True
            if any(o in href for o in RENAME):
                stats['rename'] += 1
            else:
                stats['fixed'] += 1
            return m.group(1) + '/music-library/' + urllib.parse.quote(newrel).replace('%2F', '/') + tail + m.group(3)
        stats['unresolved'] += 1
        unresolved[href] = unresolved.get(href, 0) + 1
        return m.group(0)

    s2 = ATTR.sub(sub, s)
    if dirty[0] and APPLY:
        open(p, 'w', encoding='utf-8').write(s2)

print(json.dumps(stats, ensure_ascii=False))
for k, v in sorted(unresolved.items(), key=lambda x: -x[1])[:10]:
    print('仍無法解析', v, k[:120])
print('APPLY' if APPLY else 'DRY-RUN')
