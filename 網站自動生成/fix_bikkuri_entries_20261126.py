import re, sys
P='罐頭音樂研究所/圖書館音樂/dl-music/jpx-pro-vol4/bikkuri-train-yamato-yuko/index.html'
s=open(P,encoding='utf-8').read()
orig=s

# 1) 移除誤植的第一個殘缺 <li>（缺開頭 <，且無 lbl）
pat = re.compile(r'(<ul class="entries">\s*)</?li><span class="u4line"><a href="([^"]+)">([^<]+)</a></span></li>')
m = pat.search(s)
print('broken item found:', bool(m))
if m:
    s = s[:m.start()] + m.group(1) + s[m.end():]

# 2) 標記改為只留單元名
s = s.replace('<span class="lbl">（YOYO點點名 專輯1 - 親子搖擺童樂會 - 10 泡泡 ROCK&#x27; N ROLL）</span>',
              '<span class="lbl">（10 泡泡 ROCK&#x27; N ROLL）</span>')
# 3) 奇妙莊園那列多一個 </span>
s = s.replace('<span class="lbl">（刺激100）</span></span></li>',
              '<span class="lbl">（刺激100）</span></li>')

if '--apply' in sys.argv and s!=orig:
    open(P,'w',encoding='utf-8').write(s)
    print('written')
# verify
body = s[s.find('<ul class="entries">\n<li><span class="u4line">'):]
print(re.sub(r'https?://\S+','URL', body[:400]))
print('lbl count:', s.count('class="lbl"'))
