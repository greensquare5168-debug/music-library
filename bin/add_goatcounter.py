#!/usr/bin/env python3
"""全站插入 GoatCounter 追蹤碼（idempotent）。

用法:
  python3 bin/add_goatcounter.py --code bob51688 [--dry-run]

規則:
  - 只處理 git 追蹤的 *.html
  - 已含 gc.zgo.at 者跳過
  - 插在第一個 </head> 前（沒有 </head> 就插在 <body> 前）
  - 路徑一律用相對路徑 gc.js（GitHub Pages 在 /music-library/ 子目錄）
"""
import argparse
import re
import subprocess
import sys

CFG = (
    '<script>window.goatcounter=window.goatcounter||{};'
    'window.goatcounter.path=function(p){return p;};</script>\n'
    '<script data-goatcounter="https://{code}.goatcounter.com/count" '
    'async src="https://gc.zgo.at/count.js"></script>\n'
)


def rel_prefix(path: str) -> str:
    depth = path.count('/')
    return '../' * depth


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--code', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    raw = subprocess.run(['git', 'ls-files', '-z', '*.html'],
                         capture_output=True).stdout
    files = [p.decode('utf-8') for p in raw.split(b'\0') if p]

    changed, skipped, failed = 0, 0, []
    for f in files:
        try:
            with open(f, encoding='utf-8') as fh:
                html = fh.read()
        except Exception as e:  # noqa: BLE001
            failed.append((f, str(e)))
            continue

        if 'goatcounter' in html or 'gc.zgo.at' in html:
            skipped += 1
            continue

        snip = CFG.replace('{code}', args.code)
        m = re.search(r'</head>', html, re.I)
        if m:
            new = html[:m.start()] + snip + html[m.start():]
        else:
            mb = re.search(r'<body', html, re.I)
            if not mb:
                skipped += 1
                continue
            new = html[:mb.start()] + snip + html[mb.start():]

        if not args.dry_run:
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(new)
        changed += 1

    print('total=%d changed=%d skipped=%d failed=%d' % (len(files), changed, skipped, len(failed)))
    for f, e in failed[:10]:
        print('  FAIL', f, e)
    return 0


if __name__ == '__main__':
    sys.exit(main())
