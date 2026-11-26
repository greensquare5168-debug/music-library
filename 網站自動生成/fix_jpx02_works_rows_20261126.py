#!/usr/bin/env python3
# 作品頁(集頁)內 JPX-02 曲目列：曲名連外部YouTube/官網 → 括號專輯(不可點) → ↗ 連回本站曲目頁
# 並移除曲目頁「使用作品」列尾的 ↗（作品連結不加箭頭）
import os,re,sys,urllib.parse

APPLY='--apply' in sys.argv
SITE='/music-library/'
BASE='罐頭音樂研究所/圖書館音樂/dl-music/jpx-pro-vol2'
# 專輯頁曲名 → slug
SLUG={
 'ピエロの帽子':'clown-hat-yamato-yuko',
 'Fairytale':'thumb-princess-yamato-yuko',
 '天使の願いごと':'angels-wish-yamato-yuko',
 'ペガサスに乗って':'a-pegasus-yamato-yuko',
 'ワクワク冒険隊':'exciting-adventure-team-yamato-yuko',
 'ピエロと風船':'clown-balloon-yamato-yuko',
 '月明かりの詩人':'moonlight-poet-yamato-yuko',
 'Dolphin':'dolphin-yamato-yuko',
}
# 作品頁目前寫的英文名 → 日文名
EN2JP={
 'Clown Hat':'ピエロの帽子',
 'Thumb Princess':'Fairytale',
 "Angel's Wish":'天使の願いごと',
 'A Pegasus':'ペガサスに乗って',
 'Exciting Adventure Team':'ワクワク冒険隊',
 'Clown & Balloon':'ピエロと風船',
 'Clown &Amp; Balloon':'ピエロと風船',
 'Moonlight Poet':'月明かりの詩人',
 'Dolphin':'Dolphin',
}
def track_href(slug):
    p=os.path.join(BASE,slug)
    return SITE+urllib.parse.quote(p,safe='/')+'/'

# ① 作品頁（集頁）曲目列：加 ↗ 連回本站
row_re=re.compile(
 r'(?P<pre><li><a href="(?P<ext>https?://[^"]+)" target="_blank" rel="noopener">)'
 r'(?P<inner>[^<]+)</a>'
 r'(?P<lbl><span class="lbl">（(?P<albl>[^<]*)）</span>)'
 r'(?P<tail></li>)')
changed=0; pages=0; unk=set()
for root,dirs,files in os.walk('罐頭音樂研究所'):
    if 'index.html' not in files: continue
    if 'jpx-pro-vol2' in root: continue
    fp=os.path.join(root,'index.html')
    s=open(fp,encoding='utf-8').read()
    if 'dl.music-yamato.jp' not in s: continue
    def repl(m):
        global changed
        inner=m.group('inner')
        name=inner.split(' - ')[0].strip()
        if name not in EN2JP: unk.add(name); return m.group(0)
        jp=EN2JP[name]
        slug=SLUG.get(jp)
        if not slug: unk.add(name); return m.group(0)
        changed+=1
        return (m.group(1)+jp+'</a>'+m.group('lbl')
                +'<a class="same" href="'+track_href(slug)+'" title="查看同使用作品" '
                +'style="margin-left:6px;font-size:15px;line-height:1;color:#8a97a8;text-decoration:none">↗</a>'
                +m.group('tail'))
    s2=row_re.sub(repl,s)
    if s2!=s:
        pages+=1
        if APPLY: open(fp,'w',encoding='utf-8').write(s2)
print('作品頁曲目列 改寫',changed,'處｜',pages,'頁｜未知曲名',unk)

# ② 曲目頁「使用作品」：移除 <a class="same" ...>↗</a>
same_re=re.compile(r'<a class="same"[^>]*>[^<]*</a>')
n2=0;p2=0
for root,dirs,files in os.walk(BASE):
    if 'index.html' not in files: continue
    fp=os.path.join(root,'index.html')
    s=open(fp,encoding='utf-8').read()
    s2,c=same_re.subn('',s)
    if c:
        n2+=c;p2+=1
        if APPLY: open(fp,'w',encoding='utf-8').write(s2)
print('曲目頁移除 ↗',n2,'處｜',p2,'頁')
if not APPLY: print('（DRY-RUN，加 --apply 才寫入）')
