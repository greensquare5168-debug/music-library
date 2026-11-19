#!/usr/bin/env python3
"""依「之前的紀錄」(Google Sites 鏡像第一版, commit 8f65d69) 重排童話世界各集曲目。
只調整 li 的順序與所屬段落（片頭曲／第一故事／廣告後片段／第二故事／片尾曲），
不改任何曲目連結、作者、專輯標籤。
用法:
  python3 bin/reorder_by_record.py            # 只報告
  python3 bin/reorder_by_record.py --apply    # 實際寫入
  python3 bin/reorder_by_record.py --apply --only 04,05
"""
import subprocess, re, glob, html, sys, os

OLDCOMMIT = '8f65d69d80b4'
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = sorted(glob.glob(os.path.join(BASE, '罐頭音樂研究所/yoyotv/yoyo童話世界/*/index.html')))
SKIP = {'01', '02'}          # 孝瓏指定：第 1、2 集不動
BLANK = '<li class="blankline" style="list-style:none;border:0;padding:0">&nbsp;</li>'
BLANK_DIV = '<div class="blankline">&nbsp;</div>'


def norm(s):
    s = html.unescape(s)
    s = s.split('（')[0]
    s = re.sub('↗', '', s)
    s = re.sub(r'^(片頭曲|片尾曲)', '', s).strip()
    t = s.split(' - ')[0]
    t = t.lower().replace('\u2019', "'").replace('\u2018', "'")
    return re.sub(r"[^a-z0-9\u3040-\u30ff\u4e00-\u9fff]+", '', t)


def old_segments(blob):
    """回傳 [(story, norm_title)]；story 0=片頭 1=第一故事 2=第二故事"""
    body = blob[blob.index('<div class="album-card">'):blob.index('</main>')]
    b = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    items, heading = [], None
    for m in re.finditer(r'<div class="unit[^"]*"[^>]*>(?:<[^>]+>)*([^<]*)</div>|<li[^>]*>(.*?)</li>', b, re.S):
        if m.group(1) is not None:
            heading = m.group(1).strip()
            continue
        x = html.unescape(re.sub('<[^>]+>', '', m.group(2))).strip()
        if x and x != '\xa0':
            items.append((heading, x))
    out, story = [], 1
    for h, x in items:
        if h and ('休息一下' in h or '廣告後片段' in h):
            story = 2
            out.append((2, norm(x)))
        elif h is None or x.startswith('片頭曲'):
            out.append((0, norm(x)))
        elif x.startswith('片尾曲'):
            out.append((2, norm(x)))
        else:
            out.append((story, norm(x)))
    return out


def sec_of(units):
    """依目前段落標題推算曲目所屬段落：0=片頭 1=第一故事 2=第二故事"""
    names = [u for u in units]
    if not names:
        return 0
    if '廣告後片段' in names:
        return 2 if names.index('廣告後片段') < len(names) - 1 else 2
    return 0 if len(names) == 1 else 1


def parse_page(blob):
    body = blob[blob.index('<div class="album-card">'):blob.index('</main>')]
    head = body[:body.index('</div>', body.index('<div class="ytframe">')) + len('</div>')]
    div_m = re.search(r'<div class="unit ad" data-label="廣告後片段"[^>]*>廣告後片段</div>', body)
    divider = div_m.group(0) if div_m else ''
    units, items = [], []
    for m in re.finditer(r'<div class="unit([^"]*)"[^>]*>(?:<[^>]+>)*([^<]*)</div>|<li[^>]*>.*?</li>', body, re.S):
        if m.group(2) is not None:
            units.append(m.group(2).strip())
            continue
        li = m.group(0)
        if 'class="blankline"' in li:
            continue
        t = re.sub('<[^>]+>', '', li).strip()
        if t:
            items.append({'li': li, 'n': norm(t), 'sec': sec_of(units)})
    story1 = units[1] if len(units) > 1 else ''
    story2 = units[3] if len(units) > 3 else ''
    return head, divider, story1, story2, items


def rebuild(head, divider, story1, story2, old, items):
    queues = {}
    for i, it in enumerate(items):
        queues.setdefault(it['n'], []).append(i)
    ptr = {k: 0 for k in queues}
    placed = {0: [], 1: [], 2: []}          # (原index, li)
    used = set()
    for story, n in old:
        if n not in queues or ptr[n] >= len(queues[n]):
            continue
        idx = queues[n][ptr[n]]
        ptr[n] += 1
        li = items[idx]['li']
        if 'r-outro' in li:                 # 片尾曲樣式固定留最後
            continue
        placed[story].append((idx, li))
        used.add(idx)

    # 紀錄沒有的曲目：留在它原本所屬的段落，按原順序安插
    for i, it in enumerate(items):
        if i in used or 'r-outro' in it['li']:
            continue
        sec = it['sec']
        lst = placed[sec]
        pos = next((k for k, (j, _) in enumerate(lst) if j > i), len(lst))
        lst.insert(pos, (i, it['li']))

    def plain(story):
        return [li for _, li in sorted(placed[story])]

    outro = [it['li'] for it in items if 'r-outro' in it['li']]
    intro, s1, s2 = plain(0), plain(1), plain(2)

    def block(lst, tail=False):
        return '<ul class="entries">' + ''.join(lst) + (BLANK if tail else '') + '</ul>'

    out = ['<div class="unit ad">片頭曲</div>', block(intro),
           BLANK_DIV + f'<div class="unit" data-label="{story1}">{story1}</div>',
           block(s1, tail=True),
           divider,
           f'<div class="unit" data-label="{story2}">{story2}</div>',
           block(s2 + outro, tail=not outro)]
    return ''.join(out)


def main():
    apply = '--apply' in sys.argv
    only = None
    if '--only' in sys.argv:
        i = sys.argv.index('--only')
        only = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    for p in PAGES:
        ep = p.split('-第')[1][:2]
        if ep in SKIP or (only and ep not in only.split(',')):
            continue
        blob = open(p, encoding='utf-8').read()
        rel = os.path.relpath(p, BASE)
        oldblob = subprocess.run(['git', 'show', f'{OLDCOMMIT}:{rel}'], cwd=BASE,
                                 capture_output=True, text=True).stdout
        old = old_segments(oldblob)
        head, divider, story1, story2, items = parse_page(blob)
        body_new = rebuild(head, divider, story1, story2, old, items)
        start = blob.index('<div class="album-card">')
        end = blob.index('</div></div></div>\n</main>')
        new_blob = blob[:start] + head + body_new + blob[end:]
        def ntracks(x):
            return len([l for l in re.findall(r'<li[^>]*>', x) if 'blankline' not in l])
        n_old, n_new = ntracks(blob), ntracks(new_blob)
        if n_old != n_new:
            print(f'ep{ep} ⚠ 曲目數不一致 {n_old}→{n_new}，跳過')
            continue
        print(f'ep{ep}: 曲目 {n_old}→{n_new} OK')
        if apply:
            open(p, 'w', encoding='utf-8').write(new_blob)


if __name__ == '__main__':
    main()
