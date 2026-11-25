
function fitSrc(){
  // 孝瓏 2026-11-07：所有來源網站內嵌視窗一律「固定高度」
  // ＝正常瀏覽器去掉網址列與下方工具列後的可視範圍（樣張 1920×869 物理 = CSS 1536×695，2.21:1）
  var H_FIX=695;
  var fr=document.querySelectorAll('.srcframe');
  for(var i=0;i<fr.length;i++){
    var f=fr[i], ifr=f.getElementsByTagName('iframe')[0];
    if(!ifr) continue;
    if(f.getAttribute('data-nofit')){        // 對方網站拒絕內嵌：維持原比例填滿框，不再縮放
      ifr.style.width='100%'; ifr.style.height='100%'; ifr.style.transform='none';
      continue;
    }
    var fw=f.clientWidth;
    if(!fw) continue;
    var src=(ifr.getAttribute('src')||'');
    var W=1536;
    if(src.indexOf('groove-musicsearch')>=0) W=1280;      // Groovers 滿版對齊（孝瓏 2026-10-18）
    if(src.indexOf('reliable-source.co.uk')>=0) W=1920;   // RSM 樣張 1920×918
    if(src.indexOf('euromusicro')>=0) W=1140;              // euromusicro 用 Bootstrap 4 容器 1140，避免右側多一塊白
    ifr.style.width=W+'px'; ifr.style.height=H_FIX+'px';
    var s=fw/W;
    ifr.style.transform='scale('+s+')'; ifr.style.transformOrigin='top left';
    f.style.height=Math.round(H_FIX*s)+'px';
  }
}
document.addEventListener('DOMContentLoaded',fitSrc);
window.addEventListener('load',fitSrc);
window.addEventListener('resize',fitSrc);
function fitWin(){
  // 來源網站「窗口」：固定設計寬度 1200 內部渲染，再等比縮放 + 垂直裁切到起始區段
  // 用法：<div class="srcwin" data-design="1200" data-offset="340" data-fh="2400">
  // 2026-11-21 孝瓏：「跳轉之後，還能再滑動」→ 窗口內可再上下滑動看更多內容
  var ws=document.querySelectorAll('.srcwin');
  for(var i=0;i<ws.length;i++){
    var w=ws[i], f=w.getElementsByTagName('iframe')[0];
    if(!f) continue;
    var cw=w.clientWidth; if(!cw) continue;
    var view=w.clientHeight; if(!view) continue;
    var design=parseFloat(w.getAttribute('data-design'))||1200;
    var off=parseFloat(w.getAttribute('data-offset'))||0;
    var fh=parseFloat(w.getAttribute('data-fh'))||2400;
    // 可滑動範圍：起始位置 off → 最多滑到 iframe 底部（留一屏可視高度）
    var maxOff=Math.max(0, fh-view/(cw/design));
    if(off>maxOff) off=maxOff;
    w.setAttribute('data-off', off);
    w.setAttribute('data-maxoff', maxOff);
    w.setAttribute('data-scale', cw/design);
    if(!w.getAttribute('tabindex')) w.setAttribute('tabindex','0');
    var s=cw/design;
    f.style.width=design+'px';
    f.style.height=fh+'px';
    f.style.transformOrigin='top left';
    f.style.transform='translateY('+(-off*s)+'px) scale('+s+')';
  }
}
// 窗口滾動：滑鼠滾輪 / 拖曳 / 方向鍵 → 在窗口範圍內上下移動 iframe（頁面捲動不受影響
(function(){
  function shift(w,dy){
    var s=parseFloat(w.getAttribute('data-scale'))||1;
    var off=parseFloat(w.getAttribute('data-off'))||0;
    var maxOff=parseFloat(w.getAttribute('data-maxoff'))||0;
    var next=Math.min(maxOff, Math.max(0, off + dy/s));
    if(next===off) return false;
    w.setAttribute('data-off', next);
    var f=w.getElementsByTagName('iframe')[0];
    if(f) f.style.transform='translateY('+(-next*s)+'px) scale('+s+')';
    return true;
  }
  function bind(w){
    if(w.getAttribute('data-wbind')) return;
    w.setAttribute('data-wbind','1');
    // 一次滾輪只移動「滾輪量 × 0.6」（除以縮放比換算成來源頁像素），
    // 並限制單次上限，避免一次滑到底（2026-11-21 實測：deltaY 400 會直接跳到最底）
    w.addEventListener('wheel', function(e){
      var d=e.deltaY;
      if(e.deltaMode===1) d*=20; else if(e.deltaMode===2) d*=w.clientHeight;
      var step=Math.max(-240, Math.min(240, d*0.6));
      if(shift(w, step)) e.preventDefault();
    }, {passive:false});
    var down=false, lastY=0;
    w.addEventListener('mousedown', function(e){ down=true; lastY=e.clientY; w.style.cursor='grabbing'; });
    w._mousemove=function(e){ if(!down) return; shift(w, lastY-e.clientY); lastY=e.clientY; };
    w._mouseup=function(){ if(down){ down=false; w.style.cursor=''; } };
    window.addEventListener('mousemove', w._mousemove);
    window.addEventListener('mouseup', w._mouseup);
    w.addEventListener('keydown', function(e){
      if(e.key==='ArrowDown'){ if(shift(w,120)) e.preventDefault(); }
      else if(e.key==='ArrowUp'){ if(shift(w,-120)) e.preventDefault(); }
      else if(e.key==='PageDown'){ if(shift(w,w.clientHeight)) e.preventDefault(); }
      else if(e.key==='PageUp'){ if(shift(w,-w.clientHeight)) e.preventDefault(); }
    });
  }
  function boot(){
    var ws=document.querySelectorAll('.srcwin');
    for(var i=0;i<ws.length;i++) bind(ws[i]);
  }
  document.addEventListener('DOMContentLoaded',boot);
  window.addEventListener('load',boot);

  // ── 2026-11-21 修正：來源網站「有自己捲軸的區塊」會把滾輪事件吃光，頁面上攔不到 ──
  // 做法：在窗口外面蓋一層透明「捲動罩」，滑鼠在窗口上時一律由我方接管滾輪/拖曳，
  //       要點播放器時點罩子 = 穿過同一點到 iframe（同一位置元素，座標一致 → 點擊命中同一目標）
  // 關鍵：罩子只有在 iframe 跨網域無法讀取時才加（同源照舊直接作用）
  function overbox(){
    var ws=document.querySelectorAll('.srcwin');
    for(var i=0;i<ws.length;i++){
      var w=ws[i]; if(w.getAttribute('data-ov')) continue;
      var f=w.getElementsByTagName('iframe')[0]; if(!f) continue;
      var box=document.createElement('div');
      box.className='srcov';   // 一律加罩（跨網域時頁面上的 wheel 攔不到，只有罩子可靠）
      box.style.cssText='position:absolute;left:0;top:0;right:0;bottom:0;z-index:5;background:transparent;cursor:grab';
      w.appendChild(box);
      w.setAttribute('data-ov','1');
      w._wheel=function(e){
        var d=e.deltaY;
        if(e.deltaMode===1) d*=20; else if(e.deltaMode===2) d*=w.clientHeight;
        var step=Math.max(-240, Math.min(240, d*0.6));
        shift(w, step);
        e.preventDefault(); e.stopPropagation();
      };
      (function(w,box){
        // 2026-11-22 孝瓏：罩子上的點擊會被擋住 iframe 自己的滑鼠事件（游標變手但點不動）→ 一律穿透
        // 做法：罩子本身 pointer-events:none（滑鼠事件直接落到 iframe），滾輪改在「外層」攔截；
        //      拖曳＝在窗口內按住移動時暫時把罩子打開（吃掉拖曳）→ 放開後立刻收回，iframe 不受影響
        box.style.pointerEvents='none';
        w.style.touchAction='pan-y';
        w.addEventListener('wheel', w._wheel, {passive:false});
        var down=false,lastY=0,moved=0;
        function grab(e){
          if(!down) return;
          moved+=Math.abs(e.clientY-lastY);
          shift(w, lastY-e.clientY); lastY=e.clientY; e.preventDefault();
        }
        function rel(e){
          if(!down) return; down=false;
          window.removeEventListener('mousemove', grab); window.removeEventListener('mouseup', rel);
        }
        // 只有「按住後移動」才視為拖曳：mousedown 不攔，讓 iframe 自己處理點擊/播放
        w.addEventListener('mousedown', function(e){
          if(e.button!==0) return;
          if(e.target && e.target.tagName==='IFRAME'){
            lastY=e.clientY; moved=0; down=true;
            window.addEventListener('mousemove', grab); window.addEventListener('mouseup', rel);
          }
        });
      })(w,box);
    }
  }
  document.addEventListener('DOMContentLoaded',overbox);
  window.addEventListener('load',overbox);
})();
document.addEventListener('DOMContentLoaded',fitWin);
window.addEventListener('load',fitWin);
window.addEventListener('resize',fitWin);
function openWin(u){
  try{
    var w=Math.min(1200,Math.round(screen.availWidth*0.8));
    var h=Math.min(800,Math.round(screen.availHeight*0.8));
    var t=Math.max(0,Math.round((screen.availHeight-h)/2));
    var l=Math.max(0,Math.round((screen.availWidth-w)/2));
    window.open(u,'ofiiiWin','width='+w+',height='+h+',top='+t+',left='+l+',resizable=yes,scrollbars=yes');
  }catch(e){ window.open(u,'_blank'); }
  return false;
}
(function(){
  var q=document.getElementById('q'); if(!q) return;
  var idx=null, box=document.createElement('div');
  box.className='sresults'; q.parentNode.appendChild(box);
  function injectBase(){
    var m=location.pathname.indexOf('/罐頭音樂研究所');
    return m>=0? location.pathname.slice(0,m)+'/' : '/';
  }
  function load(){
    if(idx) return Promise.resolve(idx);
    return fetch(injectBase()+'search-index.json?v=20261030b').then(function(r){return r.json();}).then(function(j){idx=j;return j;});
  }
  q.addEventListener('input',function(){    var s=q.value.trim().toLowerCase();
    if(s.length<1){ box.innerHTML=''; return; }
    load().then(function(list){
      var hits=list.filter(function(x){return (x.t+' '+(x.k||'')).toLowerCase().includes(s);}).sort(function(a,b){return (b.t.toLowerCase().includes(s)?1:0)-(a.t.toLowerCase().includes(s)?1:0);}).slice(0,40);
      box.innerHTML=hits.map(function(x){return '<a href="'+injectBase()+x.p+'">'+x.t+'</a>';}).join('')||'<span class="muted">無結果</span>';
    });
  });
})();

// 左側清單：收合箭頭 + 分組收合（孝瓏 2026-10-08）
(function(){
  // 2026-11-04 孝瓏：「點左欄畫面會閃一下」
  // 原因：頁面靜態左欄先畫出來 → app.js 用 tree.json 重畫時把整塊清空再長出來（＝閃 2 次）
  // 解法：CSS 先隱藏左欄內容（背景卡片留著，版面不跳），等樹畫好才加 .ktree-ready 一次顯示
  function treeReady(){ document.documentElement.classList.add('ktree-ready'); try{ if(window.__markStaticCur) window.__markStaticCur(); }catch(e){} }
  var box=document.querySelector('.treebox');
  if(!box){ treeReady(); return; }
  var btn=document.createElement('button');
  btn.type='button'; btn.className='navtoggle';
  box.parentNode.insertBefore(btn, box);
  function apply(c){
    document.body.classList.toggle('nav-collapsed', c);
    btn.textContent = c ? '▶' : '◀';
    btn.title = c ? '展開左側清單' : '收合左側清單';
  }
  var st=false; try{ st=localStorage.getItem('kmtNav')==='1'; }catch(e){}
  apply(st);
  btn.addEventListener('click', function(){
    var c=!document.body.classList.contains('nav-collapsed');
    try{ localStorage.setItem('kmtNav', c?'1':'0'); }catch(e){}
    apply(c);
    if(!c && window.kmtCenterCur) setTimeout(window.kmtCenterCur, 30);
  });
  // ── 由 tree.json 畫「每一層父節點都可展開」的樹（孝瓏 2026-10-08）──
  var rawseg=location.pathname.split('/').filter(Boolean);
  if(rawseg.length && rawseg[rawseg.length-1]==='index.html') rawseg.pop();
  var segs=rawseg.map(function(x){ try{ return decodeURIComponent(x); }catch(e){ return x; } });
  var ROOTS=['罐頭音樂研究所','使用公司','知識補給站','語言學習區'], idx=-1;
  for(var i=0;i<segs.length;i++){ if(ROOTS.indexOf(segs[i])>=0){ idx=i; break; } }
  if(idx>=0){
    var base='/'+rawseg.slice(0,idx).join('/')+(idx?'/':'');   // 抓 tree.json 用原始（已編碼）路徑
    var cur=segs.slice(idx).join('/')+'/';
    var pathIsLib=/圖書館音樂\//.test(cur);
    var OPENKEY='kmt_open_nodes_v1';
    var OPEN={};
    // 2026-11-09 孝瓏：重新整理後手動展開的要收起（不讀 localStorage），只留目前頁面的路徑展開
    function saveOpen(){}   // 不持久化展開狀態
    var pathKey={};   // 由 build() 填入「當前頁的祖先鏈」，render() 共用
    var curAbs=decodeURIComponent(location.pathname).replace(/\/index\.html$/,'/');
    if(curAbs.slice(-1)!=='/') curAbs+='/';
    var linkBase=base, inLib=pathIsLib;
    function absOf(h){
      if(!h) return '';
      try{ return decodeURIComponent(new URL(linkBase+h, location.origin).pathname); }catch(e){ return h; }
    }
    // 子項標題去掉與父項重複的前綴（例：父「大頭小狀元 第3季」→ 子只顯示「第08集 洋芋片」）
    function labelOf(node,pname){
      var n=node.n||'';
      if(pname && n.indexOf(pname)===0){
        var rest=n.slice(pname.length).replace(/^[\s\-｜:：]+/,'');
        if(rest) return rest;
      }
      return n;
    }
    function render(node,ul,depth,pname){
      var li=document.createElement('li'); li.className='tnode';
      var hasC=!!(node.c&&node.c.length);
      var label=labelOf(node,pname);
      var key=node.h||node.n;
      if(hasC){
        var arw=document.createElement('span'); arw.className='arw';
        arw.textContent='▸'; li.appendChild(arw);
      }else{
        // 2026-11-09 孝瓏：「最小的分頁不用加展開箭頭」→ 沒子項只留空白對齊
        var pad=document.createElement('span');
        pad.setAttribute('style','display:inline-block;width:12px;margin-right:3px');
        li.appendChild(pad);
      }
      if(node.h){
        var a=document.createElement('a'); a.href=linkBase+node.h; a.textContent=label; a.title=node.n;
        if(absOf(node.h)===curAbs || (window.__kmtCurHref && node.h===window.__kmtCurHref)) a.className='curlink';
        li.appendChild(a);
      }else{
        var sp=document.createElement('span'); sp.className='dh'; sp.textContent=label; sp.title=node.n; li.appendChild(sp);
      }
      ul.appendChild(li);
      var kids=null;
      function toggle(open){
        if(!hasC) return;
        if(!kids){
          kids=document.createElement('ul'); kids.className='tree'; kids.style.display='none'; li.appendChild(kids);
          for(var q=0;q<node.c.length;q++){ var _k=node.c[q]; if(!inLib && _k && _k.n==='音樂圖書館') continue; render(_k,kids,depth+1,node.n); }
        }
        var show=(open===undefined)?(kids.style.display==='none'):open;
        kids.style.display=show?'':'none';
        var arw=li.querySelector('.arw');
        if(arw) arw.textContent=show?'▾':'▸';
        if(show) li.classList.add('open'); else li.classList.remove('open');
        if(show){ OPEN[key]=1; } else { delete OPEN[key]; }
        saveOpen();
      }
      if(hasC && li.querySelector('.arw')) li.querySelector('.arw').addEventListener('click',function(e){ e.preventDefault(); e.stopPropagation(); toggle(); });
      if(hasC && (OPEN[key] || pathKey[key])) toggle(true);   // 沿途父節點一律展開（緊貼）
    }
    // 只在清單「可見」時把當前那頁置中（收合狀態不動作，避免展開時跑到最下面）
    function centerCur(){
      try{
        if(!box.clientHeight){ return; }          // 清單收合中 → 不要動
        var ce=box.querySelector('a.curlink');
        if(!ce){ box.scrollTop=0; return; }
        var t=ce.offsetTop-box.clientHeight/2, mx=box.scrollHeight-box.clientHeight;
        if(t<0)t=0; if(t>mx)t=mx;
        box.scrollTop=t;
      }catch(e){}
    }
    function build(t){
      // 用「解析後的真實網址」在整棵樹裡找當前頁（最長前綴），沿途父節點自動展開
      function walk(node, chain){
        var best=null, me=chain.concat([node]), u=absOf(node.h);
        if(u && curAbs.indexOf(u)===0) best={len:u.length, chain:me};
        var kids=node.c||[];
        for(var q=0;q<kids.length;q++){
          var r=walk(kids[q], me);
          if(r && (!best || r.len>best.len)) best=r;
        }
        return best;
      }
      var hit=null;
      for(var j=0;j<t.length;j++){
        var r=walk(t[j], []);
        if(r && (!hit || r.len>hit.len)) hit=r;
      }
      // 2026-11-09 孝瓏：若只比對到很淺的節點，再用「最後一段路徑」比對（如 使用公司/公視 ↔ 罐頭音樂研究所/公視）
      {
        var segsNow=curAbs.replace(/\/$/,'').split('/').filter(Boolean);
        var tail2=segsNow.slice(-1).join('/');
        function walk2(node, chain){
          var best=null, me=chain.concat([node]), u=absOf(node.h).replace(/\/$/,'');
          if(u && u.slice(-tail2.length-1)===('/'+tail2)) best={len:u.length, chain:me};
          var kids=node.c||[];
          for(var q=0;q<kids.length;q++){ var rr=walk2(kids[q], me); if(rr && (!best || rr.len>best.len)) best=rr; }
          return best;
        }
        var hit2=null;
        for(var j2=0;j2<t.length;j2++){ var r2=walk2(t[j2], []); if(r2 && (!hit2 || r2.len>hit2.len)) hit2=r2; }
        if(hit2 && (!hit || hit2.chain.length>hit.chain.length)) hit=hit2;
      }
      // 2026-11-10：音樂圖書館首頁（品牌總覽）本身不在節點裡 → 用根節點畫（否則只剩無箭頭的靜態左欄）
      if(!hit && inLib && t && t.length){ hit={chain:[t[0]]}; }
      // 2026-11-10：靜態左欄也要標示目前所在頁（比對 pathname）
      function markStaticCur(){
        try{
          var here=decodeURIComponent(location.pathname).replace(/\/index\.html$/,'/');
          if(here.slice(-1)!=='/') here+='/';
          var as=box.querySelectorAll('a[href]');
          for(var i=0;i<as.length;i++){
            var a=as[i];
            try{
              var p=new URL(a.getAttribute('href'),location.href).pathname;
              p=decodeURIComponent(p); if(p.slice(-1)!=='/') p+='/';
              if(p===here){ a.classList.add('curlink'); }
            }catch(e){}
          }
        }catch(e){}
      }
      window.__markStaticCur=markStaticCur;
      if(!hit) return false;                  // 這頁不在樹裡 → 保留原本靜態左欄
      var root=hit.chain[0];
      window.__kmtCurHref=hit.chain[hit.chain.length-1].h||'';
      pathKey={};
      for(var q=0;q<hit.chain.length;q++){ pathKey[hit.chain[q].h||hit.chain[q].n]=1; }
      // 先在「畫面外」把整棵樹組好，最後才一次換上（避免清空→長出的中間空窗）
      var ul0=document.createElement('ul'); ul0.className='tree';
      // 2026-11-09 孝瓏：左欄不要「音樂圖書館」那一層，直接從品牌開始
      // 2026-11-10 孝瓏：左欄也不要「使用公司」那一層，直接從公司開始
      var flatten=((!root.h && root.n==='音樂圖書館') || root.n==='使用公司');
      if(flatten && root.c){
        for(var bi=0;bi<root.c.length;bi++) render(root.c[bi], ul0, 0);
      }else{
        render(root,ul0,0);
      }
      box.innerHTML=''; box.appendChild(ul0);
      treeReady();
      // 2026-11-09 孝瓏：左欄要顯示「現在這一頁」→ 畫好後置中
      try{ setTimeout(centerCur, 30); }catch(e){}
      window.kmtCenterCur=centerCur;   // 2026-11-04 不再自動捲動（避免左欄每次換頁跑位）
      return true;
    }
    if(pathIsLib){
      // 音樂圖書館：改用 tree-lib.json（品牌 → 專輯 → 曲目）
      linkBase=base+'罐頭音樂研究所/圖書館音樂/';
      fetch(base+'tree-lib.json?v=20261118a',{cache:'no-store'}).then(function(r){return r.json();}).then(function(t){
        if(!build(t)) treeReady();
      }).catch(function(){ treeReady(); });
    }else{
      fetch(base+'tree.json?v=20261118a',{cache:'no-store'}).then(function(r){return r.json();}).then(function(t){
        if(!build(t)) treeReady();
      }).catch(function(){ treeReady(); });
    }
  }else{
    treeReady();
  }
  // 2026-11-07 孝瓏：左欄品牌／專輯就地展開（點箭頭收合）
  Array.prototype.forEach.call(box.querySelectorAll('.tree li > .arw'), function(arw){
    arw.addEventListener('click', function(e){
      e.preventDefault(); e.stopPropagation();
      var li=arw.parentNode;
      var open=li.classList.toggle('open');
      arw.textContent = open ? '\u25be' : '\u25b8';
    });
  });
  Array.prototype.forEach.call(box.querySelectorAll('.tree-h'), function(h){
    var ul=h.nextElementSibling;
    if(!ul||!ul.classList||ul.className.indexOf('tree')<0) return;
    h.classList.add('tree-h-toggle');
    var arw=document.createElement('span');
    arw.className='arw'; arw.textContent='▾';
    h.insertBefore(arw, h.firstChild);
    arw.addEventListener('click', function(ev){
      ev.preventDefault(); ev.stopPropagation();
      var closed=h.classList.toggle('closed');
      arw.textContent = closed ? '▸' : '▾';
      ul.style.display = closed ? 'none' : '';
    });
  });
})();

/* 站內搜尋：導覽列搜尋框（2026-10-28） */
(function(){
  function go(inp){
    var url=inp.getAttribute('data-go')||'/music-library/搜尋/index.html';
    location.href=url+'?q='+encodeURIComponent(inp.value.trim());
  }
  document.querySelectorAll('.navsearch').forEach(function(box){
    var inp=box.querySelector('.navq'), btn=box.querySelector('.navgo');
    if(!inp) return;
    if(btn) btn.onclick=function(){ go(inp); };
    inp.addEventListener('keydown',function(e){ if(e.key==='Enter'){ e.preventDefault(); go(inp);} });
  });
})();

/* 2026-11-09 孝瓏：左上角標題加展開箭頭 → 可切換 語言學習區 / 知識補給站 */
(function(){
  var brand=document.querySelector('.site-head .brand');
  if(!brand || brand.dataset.navReady) return;
  brand.dataset.navReady='1';
  var href=brand.getAttribute('href')||'';
  var base=href.replace(/index\.html$/,'');
  var wrap=document.createElement('span');
  wrap.style.cssText='position:relative;display:inline-flex;align-items:center;gap:2px';
  brand.parentNode.insertBefore(wrap, brand);
  wrap.appendChild(brand);
  var btn=document.createElement('button');
  btn.type='button'; btn.textContent='▾';
  btn.title='切換分區';
  btn.style.cssText='border:0;background:transparent;cursor:pointer;font-size:12px;line-height:1;padding:0 2px;color:#64748b';
  wrap.appendChild(btn);
  var panel=document.createElement('div');
  panel.style.cssText='position:absolute;left:0;top:100%;margin-top:6px;min-width:168px;background:#fff;border:1px solid #e3ecf3;border-radius:10px;box-shadow:0 8px 22px rgba(16,24,40,.14);padding:6px;display:none;z-index:120';
  /* 2026-11-10：改連本站分區（與頂端橫幅同一份），不再指向外部舊站 */
  /* 2026-11-11 孝瓏：左上切換選單的「語言學習區」→ 外部 multi-language 站 */
  [['語言學習區','https://greensquare5168-debug.github.io/multi-language/'],
   ['知識補給站',base+'知識補給站/index.html']].forEach(function(it){
    var a=document.createElement('a');
    a.href=it[1];
    a.textContent=it[0];
    a.style.cssText='display:block;padding:7px 10px;border-radius:7px;color:#1f2937;text-decoration:none;font-size:13px;white-space:nowrap';
    a.onmouseover=function(){a.style.background='#f1f5f9';};
    a.onmouseout=function(){a.style.background='transparent';};
    panel.appendChild(a);
  });
  wrap.appendChild(panel);
  btn.addEventListener('click',function(e){
    e.preventDefault(); e.stopPropagation();
    panel.style.display = panel.style.display==='block' ? 'none' : 'block';
  });
  document.addEventListener('click',function(){ panel.style.display='none'; });
})();

/* 2026-11-09 孝瓏：手機版漢堡選單 */
(function(){
  if(window.innerWidth>860) return;
  var head=document.querySelector('.site-head .head-row');
  if(!head || document.querySelector('.mnav')) return;
  var btn=document.createElement('button');
  btn.type='button'; btn.className='mnav'; btn.setAttribute('aria-label','開啟選單');
  btn.textContent='☰';
  head.insertBefore(btn, head.firstChild);
  function close(){ document.body.classList.remove('mnav-open'); }
  btn.addEventListener('click', function(e){
    e.preventDefault(); e.stopPropagation();
    document.body.classList.toggle('mnav-open');
  });
  var tb=document.querySelector('.treebox');
  if(tb){ tb.addEventListener('click', function(e){ if(e.target.closest('a')) close(); }); }
  document.addEventListener('click', function(e){
    if(!document.body.classList.contains('mnav-open')) return;
    if(e.target.closest('.treebox')||e.target.closest('.mnav')) return;
    close();
  });
  window.addEventListener('resize', function(){ if(window.innerWidth>860) close(); });
})();

/* 音樂圖書館：右上隱藏「語言學習區」「知識補給站」（全站；2026-11-11 孝瓏：分開） */
(function(){
  var p;
  try { p = decodeURIComponent(location.pathname); } catch(e){ p = location.pathname; }
  var inLib = p.indexOf('/罐頭音樂研究所/') >= 0;
  document.querySelectorAll('nav.topnav a.navbtn').forEach(function(a){
    var h = '';
    try { h = decodeURIComponent(a.getAttribute('href')||''); } catch(e){ h = a.getAttribute('href')||''; }
    var isLang = h.indexOf('multi-language') >= 0 || h.indexOf('語言學習區') >= 0;
    var isKnow = h.indexOf('知識補給站') >= 0;
    if(isLang || isKnow){ a.style.display = 'none'; }
  });
})();

/* 全站會員登入入口（2026-11-17 孝瓏：登入不是只有音樂圖書館）
   在每個頁面的 header 右上角插入「登入／會員」；狀態存在 localStorage（示範版） */
(function(){
  var KEY='ml_session_v1';
  var sc=document.currentScript;
  var root=(sc&&sc.src)?sc.src.replace(/app\.js.*$/,''):'/';
  function sess(){ try{ return JSON.parse(localStorage.getItem(KEY)||'null'); }catch(e){ return null; } }
  function add(){
    var nav=document.querySelector('header .topnav');
    if(!nav||nav.querySelector('.authchip')) return;
    var s=sess();
    var on=!!(s&&s.email);
    var a=document.createElement('a');
    a.className='authchip';
    a.href=root+(on?'member.html':'login.html');
    a.textContent=on?('👤 '+(s.name||s.email)):'登入';
    a.style.cssText='display:inline-flex;align-items:center;gap:6px;text-decoration:none;'
      +'border:1px solid '+(on?'#cfe9d8':'#cfd8e3')+';background:'+(on?'#f0faf3':'#fff')+';'
      +'color:'+(on?'#15803d':'#1f2733')+';'+(on?'font-weight:600;':'')
      +'border-radius:10px;padding:9px 14px;font-size:14px;white-space:nowrap';
    var sp=nav.querySelector('.navsearch');
    if(sp) nav.insertBefore(a,sp); else nav.appendChild(a);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',add); else add();
})();

/* ---------- 站主聊天框（2026-11-18）：只有「已登入 Supabase」的訪客才載入 ---------- */
(function () {
  try {
    var has = false;
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i) || '';
      if (k.indexOf('sb-') === 0 && k.slice(-11) === '-auth-token') { has = true; break; }
    }
    if (has) import('/music-library/chat-owner.js').catch(function () {});
  } catch (e) {}
})();

/* ---------- 站主鉛筆：只有「站主本人」看得到（2026-11-23 孝瓏要求） ----------
/* ---------- 站主鉛筆：只有「站主本人」看得到（2026-11-24 孝瓏：要在目前頁直接改） ----------
   目的：每一頁右上角加一個 ✏️，點下去就在「這一頁」切換成編輯模式。
   - 判斷依據：瀏覽器裡有 Supabase 登入態（login.html 登入後會留下 sb-*-auth-token）
   - 訪客（沒登入）完全看不到
   - 2026-11-24：改成「同頁就地編輯」，不換頁、不搜尋、不跳本機後端
*/
(function(){
  var TOKEN_KEY='u4_gh_token_v1';
  var OWNER_EMAILS=['greensquare5168@gmail.com'];
  var OWNER='greensquare5168-debug', REPO='music-library', BRANCH='master';

  function sbEmail(){
    try{
      for(var i=0;i<localStorage.length;i++){
        var k=localStorage.key(i)||'';
        if(k.indexOf('sb-')===0 && k.slice(-11)==='-auth-token'){
          var o=JSON.parse(localStorage.getItem(k)||'null');
          var u=o&&(o.user||(o.currentSession&&o.currentSession.user));
          if(u&&u.email) return String(u.email).toLowerCase();
        }
      }
    }catch(e){}
    return '';
  }
  function isOwner(){ var e=sbEmail(); return !!e && OWNER_EMAILS.indexOf(e)>=0; }

  function siteRoot(){
    var sc=document.currentScript;
    return (sc&&sc.src)?new URL(sc.src).pathname.replace(/[^/]*$/,''):'/music-library/';
  }
  function pagePath(){
    var root=siteRoot(), here=location.pathname;
    var rel=(here.indexOf(root)===0)?here.slice(root.length):here.replace(/^\//,'');
    if(rel===''||rel.slice(-1)==='/') rel+='index.html';
    return rel;
  }
  function repoPath(){
    var p=pagePath();
    return p.replace(/^music-library\//,'');
  }

  /* ---------- GitHub API ---------- */
  function token(){ try{ return localStorage.getItem(TOKEN_KEY)||''; }catch(e){ return ''; } }
  function askToken(){
    var t=prompt(
      '第一次使用要貼一次 GitHub token（只存在這台電腦的瀏覽器，不會上傳到任何地方）\n\n'
      +'取得：GitHub → 右上頭像 → Settings → Developer settings\n'
      +'→ Personal access tokens → Fine-grained tokens → Generate new token\n'
      +'→ Repository access 選 Only select repositories → 勾 music-library\n'
      +'→ Permissions：Contents 設 Read and write → 產生後貼上這裡\n\n'
      +'（不貼就只能看不能存檔）','');
    if(t&&t.trim()){ localStorage.setItem(TOKEN_KEY,t.trim()); return true; }
    return false;
  }
  function headers(){
    return {'Authorization':'Bearer '+token(),'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};
  }
  function b64enc(str){
    var bytes=new TextEncoder().encode(str), bin='';
    for(var i=0;i<bytes.length;i++) bin+=String.fromCharCode(bytes[i]);
    return btoa(bin);
  }
  function b64dec(b64){
    var bin=atob(String(b64||'').replace(/\s/g,''));
    var bytes=Uint8Array.from(bin,function(c){return c.charCodeAt(0);});
    return new TextDecoder().decode(bytes);
  }
  function ghGet(path){
    return fetch('https://api.github.com/repos/'+OWNER+'/'+REPO+'/contents/'+encodeURI(path)+'?ref='+BRANCH+'&t='+Date.now(),{headers:headers()})
      .then(function(r){
        if(r.status===401||r.status===403) throw new Error('token 失效或沒權限（HTTP '+r.status+'）');
        if(r.status===404) throw new Error('檔案不存在：'+path);
        if(!r.ok) throw new Error('讀取失敗 HTTP '+r.status);
        return r.json();
      })
      .then(function(d){ return {sha:d.sha, text:b64dec(d.content)}; });
  }
  function ghPut(path, text, message, sha){
    var body={message:message, content:b64enc(text), branch:BRANCH};
    if(sha) body.sha=sha;
    return fetch('https://api.github.com/repos/'+OWNER+'/'+REPO+'/contents/'+encodeURI(path),{
      method:'PUT', headers:Object.assign({'Content-Type':'application/json'},headers()), body:JSON.stringify(body)
    }).then(function(r){
      return r.json().catch(function(){return {};}).then(function(d){
        if(!r.ok) throw new Error('存檔失敗 HTTP '+r.status+'：'+(d.message||''));
        return (d.commit&&d.commit.sha)?d.commit.sha.slice(0,7):'';
      });
    });
  }

  /* ---------- HTML 工具 ---------- */
  function unesc(x){ return String(x).replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&'); }
  function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function escT(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  var RE_UL=/<ul class="entries">([\s\S]*?)<\/ul>/g;
  var EMPTY_TIP='<p class="muted">（尚未發現使用作品）</p>';

  function parseDoc(html){
    var blocks=[], m;
    RE_UL.lastIndex=0;
    while((m=RE_UL.exec(html))) blocks.push({index:m.index,end:m.index+m[0].length,inner:m[1]});
    var usage=[];
    if(blocks.length){
      var inner=blocks[blocks.length-1].inner;
      var items=inner.match(/<li[^>]*>[\s\S]*?<\/li>/g)||[];
      usage=items.filter(function(it){ return !/srccap|srcframe|ytframe|blankline/.test(it); }).map(function(it){
        var a=it.match(/<a href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/);
        var lbl=it.match(/<span class="lbl">([\s\S]*?)<\/span>/);
        return {
          href:a?unesc(a[1]):'',
          title:a?unesc(a[2].replace(/<[^>]+>/g,'').trim()):unesc(it.replace(/<[^>]+>/g,'').trim()),
          label:lbl?unesc(lbl[1].replace(/<[^>]+>/g,'').trim()):''
        };
      });
    }
    var t=html.match(/<h1>([\s\S]*?)<\/h1>/), ar=html.match(/<div class="albumartist">([\s\S]*?)<\/div>/);
    return {
      title:t?unesc(t[1].replace(/<[^>]+>/g,'').trim()):'',
      artist:ar?unesc(ar[1].replace(/<[^>]+>/g,'').trim()):'',
      usage:usage
    };
  }
  function buildItem(u){
    var lbl=u.label?'<span class="lbl">'+escT(u.label)+'</span>':'';
    return '<li><a href="'+esc(u.href)+'">'+escT(u.title)+'</a>'+lbl+'</li>';
  }
  function applyEdits(html, data, usage){
    html=html.replace(/<h1>[\s\S]*?<\/h1>/,'<h1>'+escT(data.title)+'</h1>');
    html=html.replace(/<div class="albumartist">[\s\S]*?<\/div>/,'<div class="albumartist">'+escT(data.artist)+'</div>');
    html=html.replace(/<title>[\s\S]*?<\/title>/,'<title>'+escT(data.title)+' - '+escT(data.artist)+'｜圖書館音樂研究所</title>');
    var blocks=[], m; RE_UL.lastIndex=0;
    while((m=RE_UL.exec(html))) blocks.push({index:m.index,end:m.index+m[0].length,inner:m[1]});
    if(blocks.length){
      var last=blocks[blocks.length-1];
      var keep=(last.inner.match(/<li[^>]*>[\s\S]*?<\/li>/g)||[]).filter(function(it){
        return /srccap|srcframe|ytframe|blankline/.test(it);
      });
      var next='<ul class="entries">\n'+keep.concat(usage.map(buildItem)).join('\n')+'\n</ul>';
      html=html.slice(0,last.index)+next+html.slice(last.end);
    }else{
      var ul=usage.length?('<ul class="entries">\n'+usage.map(buildItem).join('\n')+'\n</ul>'):'';
      html=html.replace(/(<div class="albumartist">[\s\S]*?<\/div>)/,'$1'+ul);
    }
    if(usage.length){
      html=html.replace(EMPTY_TIP,'');
      html=html.split('（尚未發現使用作品）').join('');
    }else if(html.indexOf('尚未發現使用作品')<0){
      if(html.indexOf('</ul>')>=0) html=html.replace(/<\/ul>(?!([\s\S]*<\/ul>))/,'</ul>'+EMPTY_TIP);
      else html=html.replace(/(<div class="albumartist">[\s\S]*?<\/div>)/,'$1'+EMPTY_TIP);
    }
    return html;
  }

  /* ---------- 排序（照網站排法） ---------- */
  var RANK=null, RANK_P=null;
  function loadRank(){
    if(RANK) return Promise.resolve(RANK);
    if(RANK_P) return RANK_P;
    RANK_P=fetch(siteRoot()+'site-rank.json?v=20261124')
      .then(function(r){ return r.ok?r.json():{}; })
      .then(function(j){ RANK=j||{}; return RANK; })
      .catch(function(){ RANK={}; return RANK; });
    return RANK_P;
  }
  function rankKey(href){
    if(!href||href.indexOf('http')===0||href.indexOf('mailto:')===0) return '';
    var p=href.split('#')[0].split('?')[0];
    if(p.indexOf('/music-library/')===0) p=p.slice('/music-library/'.length);
    else if(p.charAt(0)==='/') return '';
    try{ p=decodeURIComponent(p); }catch(e){}
    var parts=p.replace(/\\/g,'/').split('/').filter(function(x){return x!==''&&x!=='.';}), out=[];
    for(var i=0;i<parts.length;i++){ if(parts[i]==='..') out.pop(); else out.push(parts[i]); }
    var q=out.join('/');
    if(q.slice(-5)!=='.html') q=q.replace(/\/$/,'')+'/index.html';
    return q;
  }
  function sortUsage(items){
    var r=RANK||{};
    var d=items.map(function(it,i){
      var k=rankKey(it.href), n=(k&&r[k]!=null)?r[k]:1e9;
      return {it:it,n:n,i:i};
    });
    d.sort(function(a,b){ return (a.n-b.n)||(a.i-b.i); });
    return d.map(function(x){ return x.it; });
  }

  /* ---------- 專輯頁 ✓ ---------- */
  function saveAlbumMark(rel, checked){
    var dirs=rel.split('/');
    var trackDir=dirs[dirs.length-2];
    var albumPath=dirs.slice(0,dirs.length-1).concat(['index.html']).join('/');
    return ghGet(albumPath).then(function(f){
      var re=new RegExp('(<li><a class="row"[^>]*href="[^"]*/'+trackDir.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'/">)([\\s\\S]*?)(</a></li>)');
      var m=f.text.match(re);
      if(!m) return '';
      var row=m[2];
      var YES='<span class="mark" title="有發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px;background:#eaf7ef;color:#12894a;border:1px solid #bfe6cd">✓</span>';
      var NO='<span class="mark mark-x" title="尚未發現使用作品" style="display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;padding:0;line-height:1;font-size:11px;background:#f6f8fb;color:#c0c8d4;border:1px solid #e3e8ee">✕</span>';
      var row2=checked?row.replace(/<span class="mark mark-x"[^>]*>✕<\/span>/,YES):row.replace(/<span class="mark"[^>]*>✓<\/span>/,NO);
      if(row2===row) return '';
      var next=f.text.slice(0,m.index)+m[1]+row2+m[3]+f.text.slice(m.index+m[0].length);
      return ghPut(albumPath,next,'編輯模式：'+(checked?'打勾 ':'取消打勾 ')+trackDir,f.sha);
    }).catch(function(){ return ''; });
  }

  /* ---------- 就地編輯模式（不彈面板：直接在頁面文字上改） ---------- */
  var CUR=null, DIRTY=false, PANEL=null;

  function css(){
    if(document.getElementById('u4-edit-css')) return;
    var s=document.createElement('style'); s.id='u4-edit-css';
    s.textContent=''
      +'body.u4-editing .album-card h1,body.u4-editing .album-card .albumartist,body.u4-editing .album-card ul.entries li>a,body.u4-editing .album-card ul.entries li>.lbl{outline:2px dashed #9db8e8;outline-offset:3px;border-radius:5px;cursor:text;transition:background .15s}'
      +'body.u4-editing .album-card h1:hover,body.u4-editing .album-card .albumartist:hover,body.u4-editing .album-card ul.entries li>a:hover,body.u4-editing .album-card ul.entries li>.lbl:hover{background:#f2f7ff}'
      +'body.u4-editing .album-card [contenteditable="true"]:focus{outline:2px solid #2f6feb;background:#fff;box-shadow:0 0 0 3px rgba(47,111,235,.12)}'
      +'body.u4-editing .album-card ul.entries li{position:relative}'
      +'body.u4-editing .u4-del{position:absolute;right:-6px;top:50%;transform:translateY(-50%);width:22px;height:22px;line-height:1;padding:0;border-radius:50%;border:1px solid #f3c0bb;background:#fff;color:#b42318;font-size:13px;cursor:pointer;display:none}'
      +'body.u4-editing .album-card ul.entries li:hover>.u4-del{display:block}'
      +'#u4-bar{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:99999;display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e3e8ee;border-radius:14px;box-shadow:0 10px 30px rgba(15,23,42,.18);padding:10px 14px;font-size:14px}'
      +'#u4-bar .msg{font-size:13px;color:#6b7280;max-width:46vw}'
      +'#u4-bar .msg.ok{color:#12894a}'
      +'#u4-bar .msg.err{color:#b42318}'
      +'#u4-bar button{font:inherit;padding:8px 15px;border-radius:10px;border:1px solid #2f6feb;background:#2f6feb;color:#fff;cursor:pointer}'
      +'#u4-bar button.gh{background:#fff;color:#334;border-color:#cfd8e3}'
      +'#u4-bar button:disabled{opacity:.5;cursor:not-allowed}'
      +'body.u4-editing .pencil-edit{background:#fff7e6!important;border-color:#f0c36d!important}';
    document.head.appendChild(s);
  }
  function setDirty(v){
    DIRTY=v;
    var d=document.getElementById('u4-bar-msg');
    if(d && v) d.textContent='（有未存的修改）';
  }
  var MSG_T=null;
  function panelMsg(t,ok,ms){
    var m=document.getElementById('u4-bar-msg');
    if(!m) return;
    m.textContent=t; m.className='msg '+(ok?'ok':'err');
    clearTimeout(MSG_T);
    MSG_T=setTimeout(function(){
      var mm=document.getElementById('u4-bar-msg');
      if(mm){ mm.className='msg'; mm.textContent=DIRTY?'（有未存的修改）':''; }
    }, ms||9000);
  }

  function openPanel(){
    if(PANEL) return;
    if(!isOwner()){ alert('只有站主帳號可以編輯。請先登入。'); return; }
    if(!token() && !askToken()){ alert('沒有 token 不能存檔，已取消。'); return; }
    css();
    var bar=document.createElement('div'); bar.id='u4-bar';
    bar.innerHTML=''
      +'<span style="font-weight:600">✏️ 編輯模式</span>'
      +'<span class="msg" id="u4-bar-msg"></span>'
      +'<button class="gh" id="u4-add">＋ 加一筆使用作品</button>'
      +'<button id="u4-save">💾 存檔</button>'
      +'<button class="gh" id="u4-close">完成</button>';
    document.body.appendChild(bar);
    PANEL=bar;
    document.body.classList.add('u4-editing');

    document.getElementById('u4-close').onclick=function(){
      if(DIRTY){
        if(!confirm('有未存的修改，離開會消失。要先存檔嗎？（按「取消」留下繼續編輯）')) return;
        DIRTY=false;
      }
      closePanel();
    };
    document.getElementById('u4-add').onclick=function(){ addUsageRow('', '（新的一筆）', ''); setDirty(true); };
    document.getElementById('u4-save').onclick=doSave;
    window.addEventListener('beforeunload', beforeUnload);

    loadPanel();
  }
  function beforeUnload(e){
    if(!DIRTY) return;
    e.preventDefault(); e.returnValue='有未存的修改，確定要離開嗎？';
    return e.returnValue;
  }
  function closePanel(){
    if(PANEL){ PANEL.remove(); PANEL=null; }
    document.body.classList.remove('u4-editing');
    window.removeEventListener('beforeunload', beforeUnload);
    var card=document.querySelector('.album-card');
    if(card){
      Array.prototype.forEach.call(card.querySelectorAll('[contenteditable]'),function(el){
        el.removeAttribute('contenteditable'); el.removeAttribute('spellcheck');
      });
      Array.prototype.forEach.call(card.querySelectorAll('.u4-del'),function(b){ b.remove(); });
    }
    CUR=null; DIRTY=false;
  }

  function entriesUl(){
    var uls=document.querySelectorAll('.album-card ul.entries');
    return uls.length?uls[uls.length-1]:null;
  }
  function linkArgs(a){
    // 只改文字，href 絕不動：用 data 存原 href，存檔前還原
    return a;
  }
  function makeEditable(el, hint, onInput){
    if(!el || el.getAttribute('contenteditable')==='true') return;
    el.setAttribute('contenteditable','true');
    el.setAttribute('data-u4-ed','1');
    el.setAttribute('spellcheck','false');
    if(hint) el.title=hint;
    el.addEventListener('input', function(){ setDirty(true); if(onInput) onInput(); });
    el.addEventListener('keydown', function(e){
      if(e.key==='Enter'){ e.preventDefault(); el.blur(); }
    });
    el.addEventListener('paste', function(e){
      e.preventDefault();
      var t=(e.clipboardData||window.clipboardData).getData('text');
      document.execCommand('insertText', false, t);
    });
  }
  function addUsageRow(href, title, label){
    var ul=entriesUl();
    if(!ul) return null;
    var li=document.createElement('li');
    var a=document.createElement('a');
    a.setAttribute('href', href||'#new');
    a.textContent=title||'（新的一筆）';
    li.appendChild(a);
    var sp=document.createElement('span'); sp.className='lbl'; sp.textContent=label?'（'+label+'）':'';
    li.appendChild(sp);
    var del=document.createElement('button');
    del.className='u4-del'; del.type='button'; del.title='刪掉這筆'; del.textContent='×';
    del.onclick=function(e){
      e.preventDefault(); e.stopPropagation();
      if(!confirm('刪掉「'+a.textContent+'」這一筆？存檔後就消失。')) return;
      li.remove(); setDirty(true);
    };
    li.appendChild(del);
    ul.appendChild(li);
    makeEditable(a, '可以直接改這段文字（連結不變）');
    makeEditable(sp, '用括號寫標記，例：（JPX-04 Amusement Park）');
    a.focus();
    return li;
  }

  function loadPanel(){
    var rel=repoPath();
    panelMsg('讀取中…',true,60000);
    loadRank().then(function(){ return ghGet(rel); }).then(function(f){
      var d=parseDoc(f.text);
      CUR={rel:rel, sha:f.sha, raw:f.text, usage:d.usage};
      paintEditable(d.usage.length>0);
      setDirty(false);
      panelMsg('', true, 1);
    }).catch(function(e){
      panelMsg('讀取失敗：'+e.message,false,30000);
    });
  }

  function paintEditable(hasUsage){
    var card=document.querySelector('.album-card');
    if(!card) return;
    var h1=card.querySelector('h1'), ar=card.querySelector('.albumartist');
    makeEditable(h1, '直接點這裡改曲名');
    makeEditable(ar, '直接點這裡改作者');
    var ul=entriesUl();
    if(ul){
      var lis=Array.prototype.slice.call(ul.querySelectorAll(':scope > li')).filter(function(li){
        return li.querySelector(':scope > a');
      });
      lis.forEach(function(li){
        var a=li.querySelector(':scope > a'), sp=li.querySelector(':scope > .lbl');
        if(a && !a.getAttribute('data-keep')){ a.setAttribute('data-keep', a.getAttribute('href')||''); }
        makeEditable(a, '可以直接改作品名稱（連結不變）');
        if(!sp){ sp=document.createElement('span'); sp.className='lbl'; li.appendChild(sp); }
        if(!sp.textContent || sp.textContent==='') sp.textContent='';
        makeEditable(sp, '括號標記，可留空');
        if(!li.querySelector('.u4-del')){
          var del=document.createElement('button');
          del.className='u4-del'; del.type='button'; del.title='刪掉這筆'; del.textContent='×';
          del.onclick=function(e){
            e.preventDefault(); e.stopPropagation();
            if(!confirm('刪掉「'+a.textContent+'」這一筆？存檔後就消失。')) return;
            li.remove(); setDirty(true);
          };
          li.appendChild(del);
        }
      });
    }
    if(!hasUsage){
      // 目前是「尚未發現使用作品」→ 直接放一列可編輯的空白
      if(!entriesUl() || !entriesUl().querySelector(':scope > li > a')) addUsageRow('', '（新的一筆）', '');
      setDirty(false);
    }
  }

  // 把頁面上（DOM）的改動寫回 CUR.usage：順序、刪除、文字、新增都算
  function syncUsageFromDom(){
    if(!CUR) return;
    var ul=entriesUl(), out=[];
    if(ul){
      Array.prototype.forEach.call(ul.querySelectorAll(':scope > li'), function(li){
        var a=li.querySelector(':scope > a');
        if(!a || /srccap|srcframe|ytframe|blankline/.test(li.className)) return;
        var t=(a.textContent||'').trim();
        var href=a.getAttribute('data-keep')||a.getAttribute('href')||'';
        var sp=li.querySelector(':scope > .lbl');
        var lb=sp?(sp.textContent||'').trim():'';
        lb=lb.replace(/^（/,'').replace(/）$/,'').trim();
        if(!t && !href) return;
        if(href==='#new') href='';
        out.push({href:href, title:t, label:lb});
      });
    }
    CUR.usage=out;
  }

  function readEdits(){
    var card=document.querySelector('.album-card');
    var title=(card.querySelector('h1').textContent||'').trim();
    var artist=(card.querySelector('.albumartist').textContent||'').trim();
    var ul=entriesUl(), usage=[];
    if(ul){
      Array.prototype.forEach.call(ul.querySelectorAll(':scope > li'), function(li){
        var a=li.querySelector(':scope > a');
        if(!a || /srccap|srcframe|ytframe|blankline/.test(li.className)) return;
        var t=(a.textContent||'').trim();
        var href=a.getAttribute('data-keep')||a.getAttribute('href')||'';
        var sp=li.querySelector(':scope > .lbl');
        var lb=sp?(sp.textContent||'').trim():'';
        lb=lb.replace(/^（/,'').replace(/）$/,'').trim();
        if(!t && !href) return;
        usage.push({href:href, title:t, label:lb});
      });
    }
    return {title:title, artist:artist, usage:usage};
  }

  function doSave(){
    if(!CUR) return;
    syncUsageFromDom();
    var d=readEdits();
    d.usage=CUR.usage.slice();
    if(!d.title){ panelMsg('曲名不能空白',false); return; }
    var items=d.usage.filter(function(u){ return (u.href||'').trim() && (u.title||'').trim(); });
    var dropped=d.usage.length-items.length;
    if(dropped>0 && !confirm('有 '+dropped+' 筆沒填連結或標題，會被略過。要繼續嗎？')) return;

    var btn=document.getElementById('u4-save');
    btn.disabled=true; panelMsg('存檔中…',true,60000);
    var next=applyEdits(CUR.raw,{title:d.title,artist:d.artist},sortUsage(items));
    ghPut(CUR.rel,next,'編輯模式：'+d.title+'（曲名／作者／使用作品）',CUR.sha).then(function(c1){
      return saveAlbumMark(CUR.rel, items.length>0).then(function(c2){
        return ghGet(CUR.rel).then(function(f){
          CUR.sha=f.sha; CUR.raw=f.text; CUR.usage=items;
          // 存檔後把新連結記回 data-keep，並把 #new 換成正式路徑（下次存檔才不會亂）
          var ul=entriesUl();
          if(ul){
            var lis=Array.prototype.slice.call(ul.querySelectorAll(':scope > li')).filter(function(li){ return li.querySelector(':scope > a'); });
            lis.forEach(function(li,i){
              var a=li.querySelector(':scope > a');
              if(!a) return;
              var u=items[i];
              if(u && u.href) a.setAttribute('data-keep', u.href);
            });
          }
          setDirty(false);
          panelMsg('✅ 已上線（版本 '+(c1||'—')+(c2?'／專輯 ✓ '+c2:'')+'）· 約 2 分鐘後網站更新',true,20000);
        });
      });
    }).catch(function(e){
      panelMsg('存檔失敗：'+e.message,false,30000);
    }).then(function(){ btn.disabled=false; });
  }

  /* ---------- 點頁面文字就進編輯（站主限定，不用先按 ✏️） ---------- */
  function isEditableTarget(t){
    if(!t || !t.closest) return false;
    return !!t.closest('.album-card h1, .album-card .albumartist, .album-card ul.entries li > a, .album-card ul.entries li > .lbl');
  }
  function isPencilClick(t){
    return !!(t.closest && t.closest('.pencil-edit'));
  }
  function tryInlineEdit(t){
    if(!isEditableTarget(t)) return;
    if(document.body.classList.contains('u4-editing')){
      var el=t.closest('[data-u4-ed]');
      if(el && el.getAttribute('contenteditable')==='true'){
        el.focus();
        try{ document.execCommand('selectAll',false,null); }catch(e){}
      }
      return;
    }
    if(!isOwner() || !token()) return;
    if(t.closest('a') && (t.closest('a').getAttribute('href')||'').indexOf('http')===0) return;
    if(confirm('要編輯這一頁的內容嗎？（只有你看得到，改完按存檔才會上線）')){
      openPanel();
    }
  }
  document.addEventListener('click', function(e){
    try{
      if(document.body.classList.contains('u4-editing')){
        // 編輯模式中：點頁面文字 → 聚焦到那一格
        var el=e.target.closest&&e.target.closest('.album-card h1, .album-card .albumartist, .album-card ul.entries li > a, .album-card ul.entries li > .lbl');
        if(el && el.getAttribute('contenteditable')!=='true' && PANEL){
          // 尚未被標成可編輯（例如剛載入失敗）→ 補上
          makeEditable(el,'點這裡直接改');
        }
        return;
      }
      if(!e.target.closest || e.target.closest('#u4-bar')) return;
      if(isPencilClick(e.target)) return; // 鉛筆按鈕自己處理（不要彈兩次確認）
      // 2026-11-25 孝瓏：平常點連結/文字不要問要不要編輯 → 只有按 ✏️ 才進編輯模式
      return;
    }catch(err){}
  }, true);

  /* ---------- 鉛筆按鈕 ---------- */
  function add(){
    if(!isOwner()) return;
    if(document.querySelector('.pencil-edit')) return;
    var nav=document.querySelector('header .topnav')||document.querySelector('header');
    if(!nav) return;
    var a=document.createElement('a');
    a.className='pencil-edit';
    a.href='#';
    a.title='✏️ 編輯這一頁';
    a.textContent='✏️';
    a.style.cssText='display:inline-flex;align-items:center;justify-content:center;'
      +'width:34px;height:34px;border-radius:10px;border:1px solid #cfd8e3;background:#fff;'
      +'text-decoration:none;font-size:16px;line-height:1;margin-left:6px;cursor:pointer';
    a.onmouseover=function(){a.style.background='#eef3fb';};
    a.onmouseout=function(){a.style.background='#fff';};
    a.onclick=function(e){ e.preventDefault(); openPanel(); };
    var sp=nav.querySelector('.navsearch');
    if(sp) nav.insertBefore(a,sp); else nav.appendChild(a);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',add); else add();
})();
