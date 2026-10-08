
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
    return fetch(injectBase()+'search-index.json').then(function(r){return r.json();}).then(function(j){idx=j;return j;});
  }
  q.addEventListener('input',function(){    var s=q.value.trim().toLowerCase();
    if(s.length<1){ box.innerHTML=''; return; }
    load().then(function(list){
      var hits=list.filter(function(x){return x.t.toLowerCase().includes(s);}).slice(0,40);
      box.innerHTML=hits.map(function(x){return '<a href="'+injectBase()+x.p+'">'+x.t+'</a>';}).join('')||'<span class="muted">無結果</span>';
    });
  });
})();

// 左側清單：收合箭頭 + 分組收合（孝瓏 2026-10-08）
(function(){
  var box=document.querySelector('.treebox');
  if(!box) return;
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
  });
  // ── 由 tree.json 畫「每一層父節點都可展開」的樹（孝瓏 2026-10-08）──
  var segs=location.pathname.split('/').filter(Boolean);
  if(segs.length && segs[segs.length-1]==='index.html') segs.pop();
  var ROOTS=['罐頭音樂研究所','使用公司','知識補給站','語言學習區'], idx=-1;
  for(var i=0;i<segs.length;i++){ if(ROOTS.indexOf(segs[i])>=0){ idx=i; break; } }
  if(idx>=0){
    var base='/'+segs.slice(0,idx).join('/')+(idx?'/':'');
    var cur=segs.slice(idx).join('/')+'/';
    var pathIsLib=/圖書館音樂\//.test(cur);
    fetch(base+'tree.json').then(function(r){return r.json();}).then(function(t){
      var root=null;
      for(var j=0;j<t.length;j++){ if(t[j].h===segs[idx]+'/'){ root=t[j]; break; } }
      if(!root) return;
      if(pathIsLib && root.c){
        for(var k=0;k<root.c.length;k++){ if(root.c[k].h && cur.indexOf(root.c[k].h)===0){ root=root.c[k]; break; } }
      }
      function render(node,ul,isPath){
        var li=document.createElement('li'); li.className='tnode';
        var hasC=!!(node.c&&node.c.length);
        var arw=document.createElement('span'); arw.className='arw';
        arw.textContent=hasC?'▸':'\u00a0'; li.appendChild(arw);
        if(node.h){
          var a=document.createElement('a'); a.href=base+node.h; a.textContent=node.n;
          if(node.h===cur) a.className='curlink';
          li.appendChild(a);
        }else{
          var sp=document.createElement('span'); sp.className='dh'; sp.textContent=node.n; li.appendChild(sp);
        }
        ul.appendChild(li);
        var kids=null;
        function toggle(open){
          if(!hasC) return;
          if(!kids){
            kids=document.createElement('ul'); kids.className='tree'; kids.style.display='none'; li.appendChild(kids);
            for(var q=0;q<node.c.length;q++) render(node.c[q],kids,cur.indexOf(node.c[q].h||'')===0);
          }
          var show=(open===undefined)?(kids.style.display==='none'):open;
          kids.style.display=show?'':'none';
          arw.textContent=show?'▾':'▸';
          if(show) li.classList.add('open'); else li.classList.remove('open');
        }
        arw.addEventListener('click',function(e){ e.preventDefault(); e.stopPropagation(); toggle(); });
        if(hasC && isPath) toggle(true);
      }
      var ul0=document.createElement('ul'); ul0.className='tree';
      box.innerHTML=''; box.appendChild(ul0);
      render(root,ul0,true);
    }).catch(function(){});
  }
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
