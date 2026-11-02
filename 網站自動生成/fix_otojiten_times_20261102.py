#!/usr/bin/env python3
# 音・辞典 Vol.2：曲目頁嵌入播放器 start 秒數改對齊 YouTube 說明欄時間（孝瓏 2026-11-02 14:03）
# 原本用 YouTube 章節（比說明欄少 1 秒），改成說明欄文字時間
import re, sys, unicodedata, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ALBUM = ROOT / "罐頭音樂研究所/圖書館音樂/音・辞典/on-jiten-vol2-jingle-bridge"

desc = subprocess.run(
    ["yt-dlp", "--skip-download", "--print", "description", "https://youtu.be/kCbaEsRiFhs"],
    capture_output=True, text=True, check=True).stdout

# 解析說明欄：每行「M:SS - 曲名」或 ": - 曲名"
entries = []
for line in desc.splitlines():
    m = re.match(r"^\s*(:|[0-9]+:[0-9]{2})?\s*-\s*(.+?)\s*$", line)
    if m:
        t, title = m.group(1), m.group(2)
        sec = None
        if t and t != ":":
            mm, ss = t.split(":")
            sec = int(mm) * 60 + int(ss)
        entries.append((sec, title))

print(f"說明欄曲目 {len(entries)} 筆（有時間 {sum(1 for s,_ in entries if s is not None)}）")
assert len(entries) == 84, f"說明欄曲目數 {len(entries)} != 84"

dirs = sorted([p for p in ALBUM.iterdir() if p.is_dir() and re.match(r"otj2-track-\d+$", p.name)],
              key=lambda p: int(p.name.split("-")[-1]))
assert len(dirs) == 84

changed = 0
skipped = []
for d, (sec, title) in zip(dirs, entries):
    f = d / "index.html"
    s = f.read_text(encoding="utf-8")
    m = re.search(r"(youtube\.com/embed/kCbaEsRiFhs\?start=)(\d+)", s)
    if not m:
        print("!! 找不到 start:", d.name); continue
    old = int(m.group(2))
    if sec is None:
        skipped.append((d.name, title, old))
        continue
    if old != sec:
        s = s[:m.start(2)] + str(sec) + s[m.end(2):]
        f.write_text(s, encoding="utf-8")
        changed += 1

print(f"已改 {changed} 頁；說明欄無時間（保留推算）{len(skipped)} 首")
for n, t, o in skipped:
    print(f"  {n} {t} -> {o}s")

# 驗證：重新讀回比對
bad = 0
for d, (sec, title) in zip(dirs, entries):
    s = (d / "index.html").read_text(encoding="utf-8")
    m = re.search(r"start=(\d+)", s)
    got = int(m.group(1))
    if sec is not None and got != sec:
        bad += 1
        print("MISMATCH", d.name, title, got, sec)
print("驗證不一致:", bad)
