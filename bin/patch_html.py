#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_html.py — 全站批次改 HTML 的唯一入口（強制安全寫檔）

2026-11-28 事故：批次改檔直接 open(...,'w') 覆蓋，中途出錯 → 39 集頁面被截斷
（17KB→6KB），曲目整段消失。此後所有批次改檔一律走這裡。

用法：
  # 1) 先預覽（不寫檔）
  python3 bin/patch_html.py --glob '罐頭音樂研究所/yoyotv/大頭小狀元/**/index.html' \
      --dry-run --py 'lambda t: t.replace("A","B")'

  # 2) 確認筆數正確再真跑
  python3 bin/patch_html.py --glob '...' --py 'lambda t: t.replace("A","B")'

  # 3) 指定變更前的檢查條件（不符合就跳過該檔）
  python3 bin/patch_html.py --glob '...' --require '片尾曲' --py '...'

  # 4) 也可用 sed 風格的正則替換
  python3 bin/patch_html.py --glob '...' --regex '<li class="blankline"[^>]*>&nbsp;</li>' --repl ''

安全機制（由 bin/safe_html.py 提供）：
  • 先寫暫存檔 → 驗證 → os.replace 才生效
  • 驗證：檔尾 </html>、開頭 <!DOCTYPE、<body> 存在、大小 ≥ 原檔 60%、
          li/ul/div 標籤數量不得少於原檔 98%
  • 任一檔驗證失敗 → 該檔不寫、原檔不動，最後列出所有失敗檔（exit 1）
  • 全部跑完自動再 batchcheck 一次，確認沒有檔案被寫壞

建議搭配：真跑前先 git status 乾淨（方便 revert），跑完再 bin/publish.sh。
"""
import argparse
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_html import safe_write, validate  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--glob", required=True, help="相對於專案根目錄的萬用字元")
    ap.add_argument("--py", help="Python 表達式，t 為檔案內容，回傳新內容")
    ap.add_argument("--regex", help="要替換的正則")
    ap.add_argument("--repl", default="", help="替換字串（可含 \\1 群組）")
    ap.add_argument("--require", action="append", default=[],
                    help="檔案必須包含此字串，否則跳過（可重複）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-ratio", type=float, default=None,
                    help="大小下限比例（預設 0.6）")
    args = ap.parse_args(argv[1:])

    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    files = sorted(glob.glob(os.path.join(root, args.glob), recursive=True))
    files = [f for f in files if f.endswith(".html")]
    if not files:
        print("❌ 沒有符合的檔案：%s" % args.glob)
        return 2

    if not args.py and not args.regex:
        print("❌ 要指定 --py 或 --regex")
        return 2

    fn = None
    if args.py:
        fn = eval(args.py, {"re": __import__("re")})  # noqa: S307
    else:
        import re
        pat = re.compile(args.regex)
        fn = lambda t: pat.sub(args.repl, t)  # noqa: E731

    changed = skipped = 0
    failed = []
    for p in files:
        rel = os.path.relpath(p, root)
        with open(p, encoding="utf-8") as fh:
            old = fh.read()
        if any(req not in old for req in args.require):
            skipped += 1
            continue
        try:
            new = fn(old)
        except Exception as e:  # noqa: BLE001
            failed.append((rel, "套用失敗：%s" % e))
            continue
        if new is None or new == old:
            skipped += 1
            continue
        try:
            safe_write(p, new, dry_run=args.dry_run, min_ratio=args.min_ratio)
            changed += 1
            print(("🔎 " if args.dry_run else "✅ ") + rel)
        except ValueError as e:
            failed.append((rel, str(e)))

    print("\n符合 %d 檔｜%s %d 檔｜跳過 %d 檔｜失敗 %d 檔"
          % (len(files), "可改" if args.dry_run else "已改", changed, skipped, len(failed)))
    if failed:
        print("\n❌ 失敗清單（原檔未動）：")
        for rel, why in failed:
            print("  - %s :: %s" % (rel, why))
        return 1

    if not args.dry_run:
        rc = subprocess.run([sys.executable, os.path.join(root, "bin", "safe_html.py"),
                             "batchcheck", "罐頭音樂研究所"],
                            capture_output=True, text=True)
        last = (rc.stdout or "").strip().splitlines()[-1:] or [""]
        print("事後健檢：" + last[0])
        if rc.returncode != 0:
            print(rc.stdout)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
