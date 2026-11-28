#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""safe_html.py — 批次改 HTML 的安全寫檔工具（2026-11-28 建立）

背景：2026-11-28 11:58/12:0x 兩次「補空行」批次直接用 open(...,'w') 寫檔，
      中途出錯 → 檔案被截斷（17KB → 6–7KB），39 集曲目整段消失。

規則（本模組強制執行）：
  1. 絕不直接覆蓋原檔：先寫「暫存檔」，驗證通過才 os.replace。
  2. 驗證項目：
     - </html> 必須在檔尾（容忍尾端空白）
     - 必須含 <body 與 </html>
     - 檔案大小不得小於原檔的 MIN_RATIO（預設 0.6）
     - 必須保留原有的關鍵字（片尾曲、unit、entries 等出現次數不得變 0）
     - 標籤數量不得少於原檔（li / </ul> / </div> 各自 count 不得下降超過容忍值）
  3. 驗證失敗 → 不覆蓋，明確報錯（raise），原檔保持不動。
  4. --dry-run 只驗證不寫。

用法（當程式庫）：
    from safe_html import safe_write, safe_edit
    safe_write(path, new_text)                      # 驗證後才寫
    safe_edit(path, lambda t: t.replace(a, b))       # 讀→改→驗證→寫

用法（命令列）：
    python3 bin/safe_html.py check <檔案...>          # 只檢查現況是否完整
    python3 bin/safe_html.py batchcheck <根目錄>      # 全站掃描找被截斷的檔
"""
import os
import sys
import tempfile

MIN_RATIO = 0.6      # 新檔至少要是原檔的 60%
TAG_TOLERANCE = 0.98  # 標籤數量最多只能少 2%（避免誤刪大量內容）

REQUIRED_TOKENS = ["<body", "</html>"]
KEY_TOKENS = ["片尾曲", "class=\"entries\"", "</ul>", "</div>"]


def _count(text, token):
    return text.count(token)


def validate(old_text, new_text, path="?"):
    """回傳 (ok, reasons)。ok=False 代表這份新內容不可寫入。"""
    reasons = []
    if not new_text or not new_text.strip():
        return False, ["內容為空"]

    tail = new_text.rstrip()[-40:]
    if "</html>" not in tail:
        reasons.append("檔尾找不到 </html>（疑似被截斷）")
    is_redirect = ('http-equiv="refresh"' in new_text
                   or "http-equiv='refresh'" in new_text)
    if not is_redirect:
        for tok in REQUIRED_TOKENS:
            if tok not in new_text:
                reasons.append(f"缺少必要標記 {tok!r}")
        if old_text and old_text.lstrip().startswith("<!DOCTYPE") \
                and not new_text.lstrip().startswith("<!DOCTYPE"):
            reasons.append("開頭 <!DOCTYPE 不見了（疑似開頭被吃掉）")

    if old_text:
        old_len, new_len = len(old_text), len(new_text)
        if old_len and new_len < old_len * MIN_RATIO:
            reasons.append(
                f"檔案大幅縮小 {old_len} → {new_len} bytes"
                f"（<{int(MIN_RATIO*100)}% 視為截斷）")

        # 關鍵字：原本有的，改完不可以完全消失
        for tok in KEY_TOKENS:
            if old_text.count(tok) and not new_text.count(tok):
                reasons.append(f"關鍵內容消失 {tok!r}")

        # 標籤數量不得明顯下降
        for tok in ["<li", "</li>", "</ul>", "</div>"]:
            o, n = _count(old_text, tok), _count(new_text, tok)
            if o and n < o * TAG_TOLERANCE:
                reasons.append(f"{tok} 數量下降過多 {o} → {n}")

    return (not reasons), reasons


def safe_write(path, new_text, dry_run=False, min_ratio=None):
    """驗證後才原子寫入。驗證失敗 → raise ValueError，原檔不動。"""
    global MIN_RATIO
    if min_ratio is not None:
        MIN_RATIO = min_ratio
    old_text = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            old_text = fh.read()

    ok, reasons = validate(old_text, new_text, path)
    if not ok:
        raise ValueError("安全寫檔被擋下：%s -> %s" % (path, "；".join(reasons)))

    if dry_run:
        return True

    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".safe_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        # 暫存檔本身再驗一次（防寫入途中出錯）
        with open(tmp, encoding="utf-8") as fh:
            written = fh.read()
        ok2, reasons2 = validate(old_text, written, path)
        if not ok2:
            raise ValueError("暫存檔驗證失敗：%s -> %s" % (path, "；".join(reasons2)))
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return True


def safe_edit(path, fn, dry_run=False):
    """讀 → fn(text) → 驗證 → 寫。fn 回傳 None 視為不變更。"""
    with open(path, encoding="utf-8") as fh:
        old = fh.read()
    new = fn(old)
    if new is None or new == old:
        return False
    safe_write(path, new, dry_run=dry_run)
    return True


# ---------- 命令列 ----------
def _check_file(p):
    try:
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
    except Exception as e:  # noqa: BLE001
        return [f"讀不到：{e}"]
    bad = []
    # 轉址頁（meta refresh）本來就短，只檢查檔尾
    if 'http-equiv="refresh"' in t or "http-equiv='refresh'" in t:
        if "</html>" not in t.rstrip()[-40:]:
            bad.append("轉址頁檔尾沒有 </html>")
        return bad
    if not t.lstrip().startswith("<!DOCTYPE"):
        bad.append("開頭不是 <!DOCTYPE（疑似開頭被吃掉）")
    if "</html>" not in t.rstrip()[-40:]:
        bad.append("檔尾沒有 </html>（被截斷）")
    if "<body" not in t:
        bad.append("缺少 <body>")
    if len(t) < 1500:
        bad.append(f"檔案只有 {len(t)} bytes（疑似截斷）")
    return bad


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "check":
        rc = 0
        for p in argv[2:]:
            bad = _check_file(p)
            if bad:
                rc = 1
                print(f"❌ {p}: {'；'.join(bad)}")
            else:
                print(f"✅ {p}")
        return rc
    if cmd == "batchcheck":
        root = argv[2]
        bad_n = total = 0
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if f.endswith(".html"):
                    total += 1
                    p = os.path.join(dirpath, f)
                    bad = _check_file(p)
                    if bad:
                        bad_n += 1
                        print(f"❌ {p}: {'；'.join(bad)}")
        print(f"\n掃描 {total} 檔，異常 {bad_n} 檔")
        return 1 if bad_n else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
