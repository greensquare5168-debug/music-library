/* ===== 站上就地編輯（站主 only）｜2026-11-27 =====
   孝瓏：「應該要直接在頁上編輯才對」
   做法：在真正的頁面上按 ✏️ → 該頁文字與「使用作品」當場變成可改
        → 按「儲存」→ 寫進 Supabase site_edits（pending）→ U4 每 2 分鐘套用、commit、上線
   安全：
     - 只有站主帳號（OWNER_EMAILS）看得到 ✏️
     - 只提交白名單欄位（曲名／作者／使用作品／✓）
     - 路徑一律由 U4 端 safe_page() 驗證（必須落在 罐頭音樂研究所 底下）
     - 不 import 任何套件：直接讀 Supabase 存在 localStorage 的登入 session
*/
(function () {
  var OWNER_EMAILS = ['greensquare5168@gmail.com','Linxiaolong0395@gmail.com'];
  var SB_URL = '', SB_KEY = '';
  try { SB_URL = (window.SUPABASE_URL || '').trim(); SB_KEY = (window.SUPABASE_ANON_KEY || '').trim(); } catch (e) {}
  if (!SB_URL || SB_KEY.length < 20) return;   // 這頁沒有 supabase-config.js → 不啟用

  /* 2026-11-27 16:25 修：新版 supabase-js 把 session 存在「扁平」結構，
     舊版包在 currentSession；且過期的 token 不該算登入 → 直接重讀
     2026-11-27 16:45 再修：新版 key 可能是 sb-<ref>-auth-token（單一值）或
     sb-<ref>-auth-token.<分段序號>（大 token 被切成多段存在多個 key），
     要先把同前綴的分段組回來再 parse，否則一律 parse 失敗 → 誤判沒登入 */
  function readSessionFrom(raw) {
    var o = null;
    try { o = JSON.parse(raw || 'null'); } catch (e) { return null; }
    if (typeof o === 'string') { try { o = JSON.parse(o); } catch (e) { return null; } }
    if (!o) return null;
    var cands = [o, o.currentSession, o.session, o.data && o.data.session];
    for (var j = 0; j < cands.length; j++) {
      var s = cands[j];
      if (s && s.access_token) {
        if (s.expires_at && s.expires_at * 1000 < Date.now() - 60000) return null; // 已過期
        return s;
      }
    }
    // 有 user 但沒 token（新版偶有）→ 用 user 判斷身分
    for (var m = 0; m < cands.length; m++) {
      var c = cands[m];
      if (c && c.user && c.user.email) return { user: c.user, noToken: 1 };
    }
    return null;
  }
  function sbSession() {
    try {
      var joins = [];   // 先試「分段合併」，再試單一 key
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i) || '';
        if (k.indexOf('sb-') === 0 && /-auth-token(\.[0-9a-fA-F]+)*$/.test(k)) {
          var base = k.replace(/\.[0-9a-fA-F]+$/, '');
          if (joins.indexOf(base) < 0) joins.push(base);
        }
      }
      for (var b = 0; b < joins.length; b++) {
        var acc = '', okj = true;
        for (var j = 0; j < localStorage.length; j++) {
          var kk = localStorage.key(j) || '';
          if (kk === joins[b] || kk.indexOf(joins[b] + '.') === 0) {
            var piece = localStorage.getItem(kk);
            if (piece == null) { okj = false; break; }
            acc += piece;
          }
        }
        if (!okj) continue;
        var s2 = readSessionFrom(acc);
        if (s2) return s2;
      }
      for (var m2 = 0; m2 < localStorage.length; m2++) {
        var k2 = localStorage.key(m2) || '';
        if (k2.indexOf('sb-') === 0 && /-auth-token$/.test(k2)) {
          var s3 = readSessionFrom(localStorage.getItem(k2));
          if (s3) return s3;
        }
      }
    } catch (e) {}
    return null;
  }
  /* 2026-11-27 17:55 修（孝瓏：我已經登入了，還顯示「站主登入後可編輯」）：
     光讀 localStorage 不可靠（新版 supabase 把 token 分段存、key 名可能是 sb-<ref>-auth-token，
     也可能存到 sessionStorage）。改成：讀不到就直接問 Supabase /auth/v1/user 一次，
     拿到 email 才算數；結果快取在 window.__u4ieWho，避免每頁重問。 */
  var AUTH_URL = SB_URL.replace(/\/$/, '') + '/auth/v1/user';
  function rawKey() {
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i) || '';
        if (k.indexOf('sb-') === 0 && /-auth-token/.test(k)) return k;
      }
    } catch (e) {}
    return '';
  }
  function readFast() {
    /* 先看別頁查過的結果（同一次瀏覽有效） */
    if (window.__u4ieWho && window.__u4ieWho.exp > Date.now()) return window.__u4ieWho;
    /* 最可靠來源：app.js 用真的 Supabase client 取到的登入者 */
    if (window.__U4_ME && window.__U4_ME.email) {
      var me = { email: String(window.__U4_ME.email), isOwner: isOwnerOf(window.__U4_ME.email), exp: Date.now() + 300000 };
      window.__u4ieWho = me; return me;
    }
    var s = sbSession();
    var e = s && s.user && s.user.email ? String(s.user.email).trim() : '';
    return { email: e, isOwner: isOwnerOf(e), exp: Date.now() + (e ? 600000 : 20000) };
  }
  function isOwnerOf(e) {
    var v = String(e || '').toLowerCase();
    if (!v) return false;
    for (var i = 0; i < OWNER_EMAILS.length; i++) { if (String(OWNER_EMAILS[i]).toLowerCase() === v) return true; }
    return false;
  }
  async function verifyWho() {
    if (window.__U4_ME && window.__U4_ME.email) {
      var m0 = { email: String(window.__U4_ME.email), isOwner: isOwnerOf(window.__U4_ME.email), exp: Date.now() + 300000 };
      window.__u4ieWho = m0; return m0;
    }
    var fast = readFast();
    if (fast.email && fast.isOwner) return fast;
    var ak = rawKey();
    var at = SB_KEY;
    try { var raw = localStorage.getItem(ak) || sessionStorage.getItem(ak) || ''; } catch (e) { var raw = ''; }
    var tok = '';
    if (raw) {
      try {
        var one = JSON.parse(raw);
        if (typeof one === 'string') one = JSON.parse(one);
        var cl = [one, one && one.currentSession, one && one.session, one && one.data && one.data.session];
        for (var i = 0; i < cl.length && !tok; i++) { if (cl[i] && cl[i].access_token) tok = cl[i].access_token; }
      } catch (e) {}
    }
    if (tok) at = tok;
    var out = { email: '', isOwner: false, exp: Date.now() + 20000 };
    try {
      var r = await fetch(AUTH_URL, { headers: { apikey: SB_KEY, Authorization: 'Bearer ' + at } });
      if (r.ok) {
        var u = await r.json();
        out.email = String((u && u.email) || '');
        out.isOwner = isOwnerOf(out.email);
        if (out.isOwner) out.exp = Date.now() + 600000;
      }
    } catch (e) {}
    window.__u4ieWho = out;
    return out;
  }

  function email() {
    if (window.__U4_ME && window.__U4_ME.email) return String(window.__U4_ME.email);
    if (window.__u4ieWho && window.__u4ieWho.email) return window.__u4ieWho.email;
    var s = sbSession();
    return s && s.user && s.user.email ? String(s.user.email) : '';
  }
  function isOwner() {
    var e = email();
    if (!e) return false;
    for (var i = 0; i < OWNER_EMAILS.length; i++) { if (String(OWNER_EMAILS[i]).toLowerCase() === e) return true; }
    return false;
  }
  var PATH = (function () { try { return decodeURIComponent(location.pathname); } catch (e) { return location.pathname; } })();

  /* 除錯：把判斷結果印在 console，方便孝瓏回報 */
  try {
    var _dbgS = sbSession();
    console.info('[u4-inline] quick-read email=', email() || '(讀不到，稍後向伺服器確認)',
                 'hasToken=', !!(_dbgS && _dbgS.access_token), 'path=', PATH.slice(0, 80));
  } catch (e) {}

  /* 只在「曲目頁」啟用（路徑含 /罐頭音樂研究所/圖書館音樂/）
     2026-11-27 16:50 修：PATH 原本宣告在這行之後 → 上面 debug 那行會 ReferenceError，
     整支腳本直接掛掉（✏️ 永遠不出現）。改成先宣告、且 debug 不依賴它。 */
  if (PATH.indexOf('/罐頭音樂研究所/圖書館音樂/') < 0) return;

  /* rel：從 GitHub Pages 根算起，例如 罐頭音樂研究所/圖書館音樂/<品牌>/<專輯>/<曲目>/index.html */
  function relPath() {
    var i = PATH.lastIndexOf('/罐頭音樂研究所/');
    if (i < 0) return '';
    var r = PATH.slice(i + 1);
    if (r === '' || r.slice(-1) === '/') r += 'index.html';
    return r;
  }

  /* ── 讀頁面內容（跟 admin-edit.html 同一套解析）── */
  function pickText() {
    var sels = ['h1', '.song-title', '.track-title', 'h2'];
    for (var i = 0; i < sels.length; i++) {
      var el = document.querySelector(sels[i]);
      if (el && el.textContent.trim()) return el.textContent.trim().replace(/\s*[|｜].*$/, '').trim();
    }
    return '';
  }
  function artistEl() {
    return document.querySelector('.albumartist,.artist,.creator,.composer,[data-artist]');
  }
  function pickArtist() {
    var el = artistEl();
    if (el && el.textContent.trim()) return el.textContent.trim().replace(/^(作者|作曲|作曲者)[:：]\s*/, '');
    return '';
  }
  function pickUsage() {
    var out = [], seen = {};
    var nodes = document.querySelectorAll('.album-card li a[href], .entries li a[href], #usages a[href]');
    for (var i = 0; i < nodes.length; i++) {
      var a = nodes[i];
      var href = a.getAttribute('href') || '';
      var title = (a.textContent || '').trim();
      if (!title || !href || /^(#|javascript:)/.test(href)) continue;
      var h = href; try { h = decodeURIComponent(href); } catch (e) {}
      if (h.indexOf('罐頭音樂研究所') < 0) continue;
      if (/\.(jpg|png|mp3|pdf)$/i.test(h)) continue;
      var key = href + '|' + title;
      if (seen[key]) continue;
      seen[key] = 1;
      var sib = a.nextElementSibling;
      var label = (sib && /lbl/.test(sib.className)) ? sib.textContent.replace(/^[（(]|[）)]$/g, '').trim() : '';
      out.push({ href: href, title: title, label: label });
    }
    return out;
  }

  /* ── 建立校對框（手機也好按）── */
  var CSS = ''
    + '.u4ie-btn{position:fixed;right:20px;bottom:88px;z-index:9999;display:flex;align-items:center;justify-content:center;'
    + 'width:56px;height:56px;border-radius:50%;border:0;cursor:pointer;background:linear-gradient(135deg,#7bd6a6,#37a86e);'
    + 'color:#06371f;font-size:22px;line-height:1;box-shadow:0 8px 24px rgba(20,60,40,.3)}'
    + '.u4ie-login{position:fixed;right:20px;bottom:88px;z-index:9998;font:12px/1.2 system-ui,sans-serif;'
    + 'padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.92);border:1px solid #cfd8e3;'
    + 'color:#33507a;text-decoration:none;box-shadow:0 4px 14px rgba(20,40,70,.15)}'
    + '.u4ie-login:hover{background:#eef3fb}'
    + '.u4ie-panel{position:fixed;right:16px;bottom:16px;z-index:10000;width:min(520px,calc(100vw - 24px));'
    + 'max-height:88vh;overflow:auto;background:#fff;border:1px solid #dbe4ee;border-radius:16px;'
    + 'box-shadow:0 18px 50px rgba(15,35,70,.28);font:14px/1.6 system-ui,-apple-system,"Noto Sans TC",sans-serif;color:#1f2733}'
    + '.u4ie-panel *{box-sizing:border-box}'
    + '.u4ie-hd{display:flex;align-items:center;gap:8px;padding:12px 14px;border-bottom:1px solid #eef2f7;position:sticky;top:0;background:#fff;border-radius:16px 16px 0 0}'
    + '.u4ie-hd b{font-size:15px}'
    + '.u4ie-x{margin-left:auto;border:0;background:#f3f6fa;border-radius:8px;width:32px;height:32px;font-size:16px;cursor:pointer}'
    + '.u4ie-bd{padding:12px 14px 16px}'
    + '.u4ie-bd label{display:block;font-size:12.5px;color:#5c6675;margin:10px 0 4px}'
    + '.u4ie-bd input[type=text],.u4ie-bd input[type=search]{width:100%;font:inherit;padding:9px 11px;border:1px solid #cfd8e3;border-radius:9px}'
    + '.u4ie-use{border:1px solid #e6ebf2;border-radius:11px;padding:9px;margin-bottom:8px;background:#fbfcfe}'
    + '.u4ie-del{border:1px solid #f3c0bb;background:#fff;color:#b42318;border-radius:8px;padding:6px 10px;font-size:12.5px;cursor:pointer}'
    + '.u4ie-row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}'
    + '.u4ie-go{flex:1;min-width:140px;font:inherit;font-weight:600;padding:11px 16px;border-radius:10px;border:0;'
    + 'background:linear-gradient(135deg,#7bd6a6,#37a86e);color:#04301b;cursor:pointer}'
    + '.u4ie-ghost{font:inherit;padding:10px 14px;border-radius:10px;border:1px solid #cfd8e3;background:#fff;cursor:pointer}'
    + '.u4ie-msg{margin-top:10px;font-size:13px;border-radius:9px;padding:9px 11px;display:none}'
    + '.u4ie-msg.ok{display:block;background:#eaf7ef;color:#12894a;border:1px solid #bfe6cd}'
    + '.u4ie-msg.err{display:block;background:#fdf0ef;color:#b42318;border:1px solid #f3c0bb}'
    + '.u4ie-hint{font-size:12px;color:#6b7280;margin-top:10px;line-height:1.6}'
    /* ── 全頁編輯模式（孝瓏 17:48：應該整頁變成編輯模式，不是跳小分頁）── */
    + '.u4ie-mode{background:#f2fbf6 !important}'
    + '.u4ie-mode h1,.u4ie-mode .albumartist,.u4ie-mode .artist,.u4ie-mode .creator,.u4ie-mode .composer{'
    + 'outline:2px dashed rgba(55,168,110,.85);outline-offset:4px;border-radius:4px;cursor:text;min-height:1.2em}'
    + '.u4ie-mode [data-u4ie]{}'
    + '.u4ie-mode .album-card li a.row{outline:1px dashed rgba(55,168,110,.45);outline-offset:2px;border-radius:6px}'
    + '.u4ie-mode .u4ie-use-line{outline:1px dashed rgba(47,111,235,.45);outline-offset:2px;border-radius:6px}'
    + '.u4ie-bar{position:fixed;left:0;right:0;top:0;z-index:10002;display:flex;align-items:center;gap:10px;'
    + 'padding:9px 14px;background:linear-gradient(135deg,#37a86e,#2b8a58);color:#eafff4;'
    + 'font:14px/1.3 system-ui,-apple-system,"Noto Sans TC",sans-serif;box-shadow:0 4px 16px rgba(10,40,25,.25)}'
    + '.u4ie-bar b{font-size:14.5px;color:#fff}'
    + '.u4ie-bar .u4ie-tip{font-size:12.5px;opacity:.92;margin-left:4px}'
    + '.u4ie-bar .u4ie-sp{margin-left:auto;display:flex;gap:8px}'
    + '.u4ie-bar button{font:inherit;font-size:13.5px;font-weight:600;border-radius:9px;padding:8px 14px;cursor:pointer;border:0}'
    + '.u4ie-bar .u4ie-save{background:#fff;color:#0f7a4a}'
    + '.u4ie-bar .u4ie-cancel{background:rgba(255,255,255,.22);color:#fff}'
    + '.u4ie-bar .u4ie-msg{margin:0 0 0 8px;font-size:13px;display:none;padding:5px 9px;border-radius:7px}'
    + '.u4ie-bar .u4ie-msg.ok{display:inline-block;background:#eafff4;color:#0b5f39}'
    + '.u4ie-bar .u4ie-msg.err{display:inline-block;background:#fdecea;color:#a4262c}'
    + '.u4ie-mode body{padding-top:0}'
    + 'body.u4ie-mode{padding-top:52px}'
    + '.u4ie-edited{background:#fffdf0;box-shadow:inset 0 0 0 1px #f0d98a;border-radius:4px}'
    + '.u4ie-usebox{border:1px dashed rgba(47,111,235,.5);border-radius:10px;padding:8px 10px;margin-top:8px;background:rgba(255,255,255,.7)}'
    + '.u4ie-usebox .u4ie-useitem{display:flex;gap:6px;align-items:center;margin-bottom:6px;font-size:14px}'
    + '.u4ie-usebox input{font:inherit;font-size:13.5px;border:1px solid #cfd8e3;border-radius:8px;padding:6px 9px;width:100%;max-width:100%;box-sizing:border-box}'
    + '.u4ie-usebox{}'
    + '.u4ie-usebox{max-width:100%;overflow-wrap:anywhere}'
    + '.u4ie-mode .layout{grid-template-columns:minmax(0,1fr) !important;display:block !important}'
    + '.u4ie-mode aside.treebox{display:none !important}'
    + '.u4ie-mode .content{max-width:100% !important;grid-column:1/-1 !important}'
    + '.u4ie-usebox .u4ie-del{border:1px solid #f3c0bb;background:#fff;color:#b42318;border-radius:8px;padding:5px 9px;font-size:12.5px;cursor:pointer;white-space:nowrap}'
    + '.u4ie-adduse{border:1px dashed #2f6feb;background:#fff;color:#2f6feb;border-radius:8px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer}';

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }

  var panel = null, usage = [], dirty = false;

  function setMsg(t, ok) {
    var m = (EDIT && EDIT.msgEl) ? EDIT.msgEl : null;
    if (!m) return;
    m.textContent = t; m.className = 'u4ie-msg ' + (ok ? 'ok' : 'err');
  }

  function sbPost(row) {
    var s = sbSession();
    var h = { apikey: SB_KEY, 'Content-Type': 'application/json', Prefer: 'return=representation' };
    h.Authorization = 'Bearer ' + (s && s.access_token ? s.access_token : SB_KEY);
    return fetch(SB_URL.replace(/\/$/, '') + '/rest/v1/site_edits', {
      method: 'POST', headers: h, body: JSON.stringify(row)
    }).then(function (r) {
      return r.text().then(function (t) {
        var d = {}; try { d = t ? JSON.parse(t) : {}; } catch (e) { d = { message: t }; }
        if (!r.ok) throw new Error((d.message || d.hint || ('HTTP ' + r.status)) + (d.code ? ' (' + d.code + ')' : ''));
        return (Array.isArray(d) ? d[0] : d) || {};
      });
    });
  }

  function submit(kind, payload) {
    return verifyWho().then(function (who) {
      if (!who.isOwner) throw new Error('這個帳號（' + (who.email || '未登入') + '）沒有編輯權限');
      return sbPost({ kind: kind, rel: relPath(), payload: payload, status: 'pending',
                      requested_by: who.email, created_at: new Date().toISOString() });
    });
  }

  /* ── 整頁編輯：把頁面上的 h1／作者、「使用作品」清單換成可輸入的欄位 ── */
  var EDIT = null;   /* { h1, artist, usageBox, markInput, bar, msgEl, orig:{...} } */

  function markEdited(el) { if (el) el.classList.add('u4ie-edited'); }

  function fieldEl(tag, value, ph) {
    var e = document.createElement(tag);
    if (tag === 'textarea') { e.rows = 1; e.style.resize = 'vertical'; }
    e.value = value || '';
    e.placeholder = ph || '';
    e.addEventListener('input', function () { dirty = true; markEdited(e); });
    return e;
  }

  function renderUsageEditor() {
    if (!EDIT) return;
    var box = EDIT.usageBox;
    box.innerHTML = '';
    if (!usage.length) {
      var none = document.createElement('div');
      none.style.cssText = 'font-size:13px;color:#6b7280;margin-bottom:6px';
      none.textContent = '（目前沒有使用作品）';
      box.appendChild(none);
    }
    usage.forEach(function (u, i) {
      var w = el('div', 'u4ie-usebox');
      var t = el('div', 'u4ie-useitem');
      var inpTitle = document.createElement('input'); inpTitle.type = 'text';
      inpTitle.value = u.title || ''; inpTitle.placeholder = '作品標題';
      var inpHref = document.createElement('input'); inpHref.type = 'text';
      inpHref.value = u.href || ''; inpHref.placeholder = '連結網址（單集網址）';
      var inpLabel = document.createElement('input'); inpLabel.type = 'text';
      inpLabel.value = u.label || ''; inpLabel.placeholder = '括號標記（可留空）';
      inpLabel.style.maxWidth = '140px';
      var del = el('button', 'u4ie-del', '刪除');
      del.type = 'button';
      [inpTitle, inpHref, inpLabel].forEach(function (inp) {
        inp.addEventListener('input', function () { dirty = true; markEdited(inp); });
      });
      inpTitle.oninput = function () { usage[i].title = inpTitle.value; dirty = true; };
      inpHref.oninput = function () { usage[i].href = inpHref.value; dirty = true; };
      inpLabel.oninput = function () { usage[i].label = inpLabel.value; dirty = true; };
      del.onclick = function () {
        if (!confirm('刪掉這一筆使用作品？')) return;
        usage.splice(i, 1); dirty = true; renderUsageEditor();
      };
      t.appendChild(inpTitle); t.appendChild(del);
      var t2 = el('div', 'u4ie-useitem');
      t2.appendChild(inpHref);
      var t3 = el('div', 'u4ie-useitem');
      t3.appendChild(inpLabel);
      w.appendChild(t); w.appendChild(t2); w.appendChild(t3);
      box.appendChild(w);
    });
    var add = el('button', 'u4ie-adduse', '＋ 加一筆使用作品');
    add.type = 'button';
    add.onclick = function () {
      usage.push({ href: '', title: '', label: '' }); dirty = true; renderUsageEditor();
      var all = EDIT.usageBox.querySelectorAll('input');
      if (all.length) all[all.length - 3].focus();
    };
    box.appendChild(add);
  }

  function buildTopBar() {
    var bar = el('div', 'u4ie-bar');
    var b = el('b', null, '✏️ 整頁編輯模式');
    bar.appendChild(b);
    bar.appendChild(el('span', 'u4ie-tip', '直接改下面的字和「使用作品」，改完按右邊儲存'));
    var sp = el('div', 'u4ie-sp');
    var m = el('span', 'u4ie-msg');
    bar.appendChild(m);
    var cancel = el('button', 'u4ie-cancel', '取消');
    cancel.type = 'button';
    cancel.onclick = function () { exitEditor(!!dirty); };
    var save = el('button', 'u4ie-save', '💾 儲存並上線');
    save.type = 'button';
    save.onclick = function (e) { doSaveAll(e.currentTarget); };
    sp.appendChild(cancel); sp.appendChild(save);
    bar.appendChild(sp);
    document.body.appendChild(bar);
    EDIT.bar = bar; EDIT.msgEl = m;
    return bar;
  }

  function enterEditor() {
    if (EDIT) return;
    EDIT = { bar: null, msgEl: null, usageBox: null };
    document.body.classList.add('u4ie-mode');
    buildTopBar();

    /* 曲名：把 h1 換成輸入框（保留原本外觀） */
    var h1 = null;
    var sels = ['h1', '.song-title', '.track-title', 'h2'];
    for (var i = 0; i < sels.length; i++) { var q = document.querySelector(sels[i]); if (q && q.textContent.trim()) { h1 = q; break; } }
    EDIT.h1 = h1;
    if (h1) {
      var tv = pickText();
      var tInp = fieldEl('input', tv, '曲名');
      tInp.type = 'text';
      tInp.style.cssText = 'font:inherit;font-size:1em;font-weight:700;width:100%;max-width:520px;'
        + 'border:1px solid #37a86e;border-radius:8px;padding:6px 10px;background:#fff';
      tInp.setAttribute('data-u4ie', 'title');
      h1.style.display = 'none';
      h1.parentNode.insertBefore(tInp, h1.nextSibling);
      EDIT.titleInput = tInp;
    }

    /* 作者 */
    var aEl = artistEl();
    EDIT.artistEl = aEl;
    if (aEl) {
      var av = pickArtist();
      var aInp = fieldEl('input', av, '作者');
      aInp.type = 'text';
      aInp.style.cssText = 'font:inherit;font-size:1em;width:100%;max-width:420px;'
        + 'border:1px solid #37a86e;border-radius:8px;padding:5px 9px;background:#fff;margin-top:6px';
      aInp.setAttribute('data-u4ie', 'artist');
      aEl.style.display = 'none';
      aEl.parentNode.insertBefore(aInp, aEl.nextSibling);
      EDIT.artistInput = aInp;
    }

    /* 使用作品：找原清單容器，改成可編輯（保留原本連結顯示讓孝瓏對照） */
    usage = pickUsage();
    /* 放在「第一個使用作品區塊」之前（表格後面），避免每列都出現一個編輯框 */
    var firstUse = null;
    var probe = document.querySelectorAll('.album-card li a[href], .entries li a[href]');
    if (probe.length) firstUse = probe[0].closest('li') || probe[0];
    var anchorBox = firstUse ? firstUse.parentNode
        : (document.querySelector('.album-card') || document.querySelector('.content') || document.querySelector('main') || document.body);
    var wrap = el('div', 'u4ie-usebox');
    wrap.style.background = '#fff';
    wrap.innerHTML = '<div style="font-weight:700;font-size:14px;color:#1f2733;margin-bottom:8px">使用作品</div>';
    var ub = el('div');
    wrap.appendChild(ub);
    if (firstUse && firstUse.parentNode && firstUse.tagName === 'LI') anchorBox.insertBefore(wrap, firstUse);
    else anchorBox.appendChild(wrap);
    EDIT.usageBox = ub;
    renderUsageEditor();

    /* 專輯頁打勾 */
    var mk = el('div');
    mk.style.cssText = 'margin-top:10px;display:flex;align-items:center;gap:8px;font-size:14px;color:#1f2733';
    var cb = document.createElement('input'); cb.type = 'checkbox';
    cb.style.cssText = 'width:20px;height:20px;accent-color:#37a86e';
    cb.checked = usage.length > 0;
    cb.addEventListener('change', function () { dirty = true; });
    EDIT.markInput = cb;
    var lb = document.createElement('label');
    lb.textContent = '這首有使用作品（專輯頁打勾）';
    mk.appendChild(cb); mk.appendChild(lb);
    wrap.appendChild(mk);

    dirty = false;
    var btn = document.querySelector('.u4ie-btn');
    if (btn) { btn.textContent = '✕'; btn.title = '離開編輯模式'; }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function exitEditor(confirmFirst) {
    if (!EDIT) return;
    if (confirmFirst && dirty && !confirm('有還沒存的修改，確定離開編輯模式？')) return;
    if (EDIT.titleInput) { EDIT.titleInput.remove(); }
    if (EDIT.h1) EDIT.h1.style.display = '';
    if (EDIT.artistInput) { EDIT.artistInput.remove(); }
    if (EDIT.artistEl) EDIT.artistEl.style.display = '';
    /* 移除使用作品編輯框（找 .u4ie-usebox 內含「使用作品」標題那個） */
    var boxes = document.querySelectorAll('.u4ie-usebox');
    for (var i = 0; i < boxes.length; i++) {
      if (boxes[i].parentNode) boxes[i].parentNode.removeChild(boxes[i]);
    }
    if (EDIT.bar) EDIT.bar.remove();
    document.body.classList.remove('u4ie-mode');
    EDIT = null; dirty = false;
    var btn = document.querySelector('.u4ie-btn');
    if (btn) { btn.textContent = '✏️'; btn.title = '就地編輯這一頁（站主）'; }
  }

  async function doSaveAll(btnEl) {
    if (!EDIT) return;
    var go = btnEl || (EDIT.bar && EDIT.bar.querySelector('.u4ie-save'));
    var title = (EDIT.titleInput ? String(EDIT.titleInput.value || '') : pickText()).trim();
    var artist = (EDIT.artistInput ? String(EDIT.artistInput.value || '') : pickArtist()).trim();
    var items = usage.filter(function (u) { return (u.href || '').trim() && (u.title || '').trim(); });
    if (items.length !== usage.length) {
      if (!confirm('有 ' + (usage.length - items.length) + ' 筆沒填連結或標題，會略過。要繼續嗎？')) return;
    }
    if (go) { go.disabled = true; go.textContent = '送出中…'; }
    var sent = 0, errs = [];
    try {
      try { await submit('save_title', { title: title, artist: artist }); sent++; }
      catch (e) { errs.push('曲名／作者：' + e.message); }
      try { await submit('save_usage', { items: items }); sent++; }
      catch (e) { errs.push('使用作品：' + e.message); }
      try { await submit('save_mark', { checked: EDIT.markInput ? EDIT.markInput.checked : (usage.length > 0) }); sent++; }
      catch (e) { errs.push('✓：' + e.message); }
      if (errs.length) setMsg('部分失敗（成功 ' + sent + ' 項）— ' + errs.join('；'), false);
      else {
        dirty = false;
        setMsg('✅ 已送出 ' + sent + ' 項修改，約 1–3 分鐘官網更新（按重新整理可看結果）。', true);
      }
    } finally {
      if (go) { go.disabled = false; go.textContent = '💾 儲存並上線'; }
    }
  }

  /* 2026-11-27：站主沒登入時，不再「整個消失」→ 顯示一顆淡色提示，點下去去登入 */
  function showLoginHint(em) {
    var box = document.querySelector('.u4ie-login');
    if (box) { if (em) box.title = '目前登入帳號：' + em; return; }
    var label = (em && em !== '(未登入/讀不到)') ? '🔑 登入中（' + em + '）但沒有編輯權限' : '🔑 站主登入後可編輯';
    var a = el('a', 'u4ie-login', label);
    a.href = '/music-library/login.html';
    a.title = '用站主帳號登入後，右上角會出現 ✏️ 就地編輯';
    document.body.appendChild(a);
  }

  function addButton(who) {
    if (document.querySelector('.u4ie-btn')) return;
    var own = who ? who.isOwner : isOwner();
    var em = (who ? who.email : email()) || '(未登入/讀不到)';
    if (!own) {
      showLoginHint(em);
      /* 已登入但不是站主 → 標明是哪個帳號，方便一眼看出問題 */
      var a = document.querySelector('.u4ie-login');
      if (a) a.title = '目前登入帳號：' + em;
      return;
    }
    var b = el('button', 'u4ie-btn', '✏️');
    b.type = 'button';
    b.title = '就地編輯這一頁（站主）';
    b.onclick = function () {
      if (EDIT) { exitEditor(true); return; }
      enterEditor();
    };
    document.body.appendChild(b);
  }

  /* 2026-11-27 17:10 修：腳本可能在 <head> 還沒解析完就執行 → document.head 是 null，
     appendChild 直接丟錯、整支腳本死掉（這才是 ✏️ 一直不出現的真正原因，前面兩次都不是）
     → 沒 head 就掛在 documentElement，兩個都沒有就等 DOM 好了再掛 */
  function injectCSS() {
    var host = document.head || document.documentElement;
    if (!host) return false;
    var style = document.createElement('style');
    style.textContent = CSS;
    host.appendChild(style);
    return true;
  }
  if (!injectCSS()) {
    document.addEventListener('DOMContentLoaded', function () { injectCSS(); boot(); });
  }

  /* 2026-11-27 17:25：載入結果做個 console 標記，出問題時一眼看得懂 */
  function boot() {
    try {
      if (window.__u4ieBooted && !document.querySelector('.u4ie-btn') && !document.querySelector('.u4ie-login')) {}
      window.__u4ieBooted = 1;
      window.__u4ieState = window.__u4ieState || { email: '(檢查中)', isOwner: false, btn: !!document.querySelector('.u4ie-btn') };
      console.info('[u4-inline] boot (will verify via /auth/v1/user)');
    } catch (e) {}
    var fast = readFast();
    addButton(fast);                                  /* 先用快的（localStorage）撐一下 */
    verifyWho().then(function (who) {
      try { window.__u4ieState.email = who.email || '(未登入)'; window.__u4ieState.isOwner = !!who.isOwner;
            console.info('[u4-inline] verified email=', window.__u4ieState.email, 'isOwner=', who.isOwner); } catch (e) {}
      var hint = document.querySelector('.u4ie-login');
      if (who.isOwner) { if (hint) hint.remove(); addButton(who); }
      else if (!document.querySelector('.u4ie-btn')) {
        if (hint) hint.remove();
        showLoginHint(who.email);
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  [400, 1200, 2500].forEach(function (t) { setTimeout(boot, t); });
  window.addEventListener('focus', boot);
})();
