#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量空行(.blankline)與上下文字的實際可見間距（px / cm）"""
import json, subprocess, sys, time, urllib.request

def post(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=120))

def get(url):
    return json.load(urllib.request.urlopen(url, timeout=60))

def start():
    gd = subprocess.Popen(['geckodriver', '--port', '4444'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            get('http://127.0.0.1:4444/status'); break
        except Exception:
            time.sleep(0.5)
    s = post('http://127.0.0.1:4444/session', {'capabilities': {'alwaysMatch': {
        'browserName': 'firefox',
        'moz:firefoxOptions': {'args': ['-headless', '--width', '1400', '--height', '1000']}}}})
    return gd, s['value']['sessionId']

JS = r"""
const out=[];
const bls=[...document.querySelectorAll('.blankline')].slice(0,6);
for(const bl of bls){
  const r=bl.getBoundingClientRect();
  const cs=getComputedStyle(bl);
  // 上一個有文字的元素
  let prev=bl.previousElementSibling, next=bl.nextElementSibling;
  const pr = prev? prev.getBoundingClientRect():null;
  const nr = next? next.getBoundingClientRect():null;
  out.push({
    tag: bl.tagName + (bl.className? '.'+bl.className.replace(/\s+/g,'.'):''),
    h: +r.height.toFixed(2),
    marginTop: cs.marginTop, marginBottom: cs.marginBottom,
    paddingTop: cs.paddingTop, paddingBottom: cs.paddingBottom,
    lineHeight: cs.lineHeight, fontSize: cs.fontSize,
    gapAbove: pr? +(r.top-pr.bottom).toFixed(2): null,
    gapBelow: nr? +(nr.top-r.bottom).toFixed(2): null,
    prevTag: prev? prev.tagName+'.'+String(prev.className).replace(/\s+/g,'.'): null,
    nextTag: next? next.tagName+'.'+String(next.className).replace(/\s+/g,'.'): null
  });
}
return out;
"""

def measure(url):
    gd, sid = start()
    try:
        post('http://127.0.0.1:4444/session/%s/url' % sid, {'url': url})
        time.sleep(2.5)
        res = post('http://127.0.0.1:4444/session/%s/execute/sync' % sid, {'script': JS, 'args': []})
        return res['value']
    finally:
        try:
            urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:4444/session/%s' % sid, method='DELETE'), timeout=10)
        except Exception:
            pass
        gd.terminate()

if __name__ == '__main__':
    for u in sys.argv[1:]:
        print('==', u)
        try:
            rows = measure(u)
        except Exception as e:
            print('ERR', e); continue
        for r in rows:
            cm = lambda p: '' if p is None else ' (%.2fcm)' % (p/96*2.54)
            print('  %s h=%.1f mt=%s mb=%s pt=%s pb=%s | gapAbove=%s%s gapBelow=%s%s' % (
                r['tag'], r['h'], r['marginTop'], r['marginBottom'], r['paddingTop'], r['paddingBottom'],
                r['gapAbove'], cm(r['gapAbove']), r['gapBelow'], cm(r['gapBelow'])))
            print('     prev=%s next=%s' % (r['prevTag'], r['nextTag']))
