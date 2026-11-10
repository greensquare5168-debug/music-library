#!/usr/bin/env bash
# 發佈前自動修 404＋檢查，通過才 push
# 用法：bin/publish.sh "commit message"
set -u
cd "$(dirname "$0")/.." || exit 1
MSG="${1:-網站更新}"

echo "① 修麵包屑層數…"; python3 bin/fix_crumb_depth.py
echo "② 重建左欄（依 tree-lib，避免幽靈/舊名連結）…"; python3 bin/rebuild_aside.py
echo "③ 修壞連結（舊品牌名／相對連結／空麵包屑）…"; python3 bin/fix_links.py
echo "④ 連結健檢…"
OUT=$(python3 bin/linkcheck_site.py | head -1)
echo "$OUT"
BROKEN=$(echo "$OUT" | python3 -c "import sys,json;print(json.load(sys.stdin).get('broken_total',0))" 2>/dev/null || echo "?")
if [ "$BROKEN" != "0" ]; then
  echo "❌ 仍有 $BROKEN 個壞連結，先不 push"
  python3 bin/linkcheck_site.py | head -20
  exit 3
fi

git add -A
if git diff --cached --quiet; then
  echo "沒有變更"
else
  git commit -q -m "$MSG"
fi
echo "⑤ push…"
git push -q origin master && echo "✅ 已推上 GitHub（等 Pages 建置）"
