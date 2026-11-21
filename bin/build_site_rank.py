import re, os, sys, urllib.parse, json
ROOT='使用公司/index.html'
def norm(base, href):
    href=href.split('#')[0]
    if href.startswith('/music-library/'):
        p=href[len('/music-library/'):]
    elif href.startswith('http'):
        return None
    else:
        p=os.path.normpath(os.path.join(os.path.dirname(base), href))
    p=urllib.parse.unquote(p)
    p=p.replace('\\','/')
    if p.endswith('/'): p+='index.html'
    if not p.endswith('index.html'): return None
    return p.lstrip('./')

rank={}; n=[0]
def walk(rel, depth=0):
    if rel in rank: return
    fp=rel
    if not os.path.exists(fp): return
    rank[rel]=n[0]; n[0]+=1
    if depth>8: return
    h=open(fp,encoding='utf-8',errors='ignore').read()
    # only listing rows
    rows=re.findall(r'<a class="row" href="([^"]+)"', h)
    for href in rows:
        t=norm(fp, href)
        if t and t not in rank: walk(t, depth+1)
walk(ROOT)
print('ranked',len(rank),file=sys.stderr)
json.dump(rank, open('/tmp/rank.json','w'), ensure_ascii=False)
