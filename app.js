
function fitSrc(){
  // 孝瓏 2026-11-07：所有來源網站內嵌視窗一律「固定高度」
  // ＝正常瀏覽器去掉網址列與下方工具列後的可視範圍（樣張 1920×869 物理 = CSS 1536×695，2.21:1）
  var H_FIX=695;
  var fr=document.querySelectorAll('.srcframe');
  for(var i=0;i<fr.length;i++){
    var f=fr[i], ifr=f.getElementsByTagName('iframe')[0];
    if(!ifr) continue;
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
  function treeReady(){ document.documentElement.classList.add('ktree-ready'); }
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
    try{ (JSON.parse(localStorage.getItem(OPENKEY)||'[]')).forEach(function(k){OPEN[k]=1;}); }catch(e){}
    function saveOpen(){ try{ localStorage.setItem(OPENKEY, JSON.stringify(Object.keys(OPEN))); }catch(e){} }
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
        if(absOf(node.h)===curAbs) a.className='curlink';
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
      if(!hit) return false;                  // 這頁不在樹裡 → 保留原本靜態左欄
      var root=hit.chain[0];
      pathKey={};
      for(var q=0;q<hit.chain.length;q++){ pathKey[hit.chain[q].h||hit.chain[q].n]=1; }
      // 先在「畫面外」把整棵樹組好，最後才一次換上（避免清空→長出的中間空窗）
      var ul0=document.createElement('ul'); ul0.className='tree';
      render(root,ul0,0);
      box.innerHTML=''; box.appendChild(ul0);
      treeReady();
      window.kmtCenterCur=centerCur;   // 2026-11-04 不再自動捲動（避免左欄每次換頁跑位）
      return true;
    }
    if(pathIsLib){
      // 音樂圖書館：改用 tree-lib.json（品牌 → 專輯 → 曲目）
      linkBase=base+'罐頭音樂研究所/圖書館音樂/';
      fetch(base+'tree-lib.json?v=20261109b').then(function(r){return r.json();}).then(function(t){
        if(!build(t)) treeReady();
      }).catch(function(){ treeReady(); });
    }else{
      fetch(base+'tree.json?v=20261109b').then(function(r){return r.json();}).then(function(t){
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
