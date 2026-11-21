#!/usr/bin/env python3
"""曲目頁「使用作品」依網站排法重排（品牌→節目→季→集）。
排法來源：從 使用公司/index.html 遞迴走 a.row 清單，DFS 順序即網站顯示順序。
用法：在 網站demo2/罐頭音樂研究所 目錄下執行 python3 ../../bin/sort_usage_by_site_order.py [--dry]
"""
import re,os,json,glob,sys,urllib.parse
DRY='--dry' in sys.argv
BASE=os.getcwd()  # 罐頭音樂研究所
def norm(base,href):
    href=href.split('#')[0].split('?')[0]
    if href.startswith('http') or href.startswith('mailto:'): return None
    if href.startswith('/music-library/'): p=href[len('/music-library/'):]
    elif href.startswith('/'): return None
    else: p=os.path.join(os.path.dirname(base),href)
    p=os.path.normpath(urllib.parse.unquote(p).replace('\\','/'))
    if not p.endswith('.html'): p=os.path.join(p,'index.html')
    return p
def build_rank():
    rank={};n=[0]
    def walk(rel,d=0):
        if rel in rank or not os.path.exists(rel) or d>10: return
        rank[rel]=n[0];n[0]+=1
        h=open(rel,encoding='utf-8',errors='ignore').read()
        for href in re.findall(r'<a class="row" href="([^"]+)"',h):
            t=norm(rel,href)
            if t and t not in rank: walk(t,d+1)
    for start in ['使用公司/index.html','使用公司/index.html'.replace('使用公司',''),'index.html']:
        if os.path.exists(start): walk(start);break
    return rank
rank=build_rank()
def tolocal(href):
    if not href.startswith('/music-library/'): return None
    q=urllib.parse.unquote(href.split('#')[0][len('/music-library/'):])
    if not q.endswith('index.html'): q=os.path.join(q,'index.html')
    return q
def key(li):
    m=re.search(r'<a href="([^"]+)"',li)
    k=tolocal(m.group(1)) if m else None
    r=rank.get(k)
    return (r if r is not None else 10**9, re.sub('<[^>]+>','',li)[:60])
UL=re.compile(r'(<ul class="entries">)(.*?)(</ul>)',re.S)
changed=[]
for p in glob.glob('圖書館音樂/**/index.html',recursive=True):
    h=open(p,encoding='utf-8').read()
    if '<h1>' not in h: continue
    def fix(m):
        items=re.findall(r'<li[^>]*>.*?</li>',m.group(2),re.S)
        kinds=['src' if ('srccap' in i or 'srcframe' in i or 'ytframe' in i) else ('blank' if 'blankline' in i else 'use') for i in items]
        uses=[i for i,k in zip(items,kinds) if k=='use']
        if len(uses)<2: return m.group(0)
        srt=sorted(uses,key=key)
        if [id(x) for x in srt]==[id(x) for x in uses]: return m.group(0)
        out=[];j=0
        for i,k in zip(items,kinds):
            if k=='use': out.append(srt[j]);j+=1
            else: out.append(i)
        return m.group(1)+''.join(out)+m.group(3)
    new=UL.sub(fix,h)
    if new!=h:
        changed.append(p)
        if not DRY: open(p,'w',encoding='utf-8').write(new)
print(('(dry) ' if DRY else '')+'changed pages:',len(changed))
for c in changed: print(' ',c)
