
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
