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
  var OWNER_EMAILS = ['linxiaolong0395@gmail.com'];
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
  function email() {
    var s = sbSession();
    return s && s.user && s.user.email ? String(s.user.email).toLowerCase() : '';
  }
  function isOwner() { return OWNER_EMAILS.indexOf(email()) >= 0; }
  /* 除錯：把判斷結果印在 console，方便孝瓏回報 */
  try {
    var _dbgS = sbSession();
    console.info('[u4-inline] email=', email() || '(未登入/讀不到)', 'isOwner=', isOwner(),
                 'hasToken=', !!(_dbgS && _dbgS.access_token), 'path=', PATH.slice(0, 80));
  } catch (e) {}

  /* 只在「曲目頁」啟用（路徑含 /罐頭音樂研究所/圖書館音樂/）
     2026-11-27 16:50 修：PATH 原本宣告在這行之後 → 上面 debug 那行會 ReferenceError，
     整支腳本直接掛掉（✏️ 永遠不出現）。改成先宣告、且 debug 不依賴它。 */
  var PATH = (function () { try { return decodeURIComponent(location.pathname); } catch (e) { return location.pathname; } })();
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
    + '.u4ie-on h1,.u4ie-on .albumartist,.u4ie-on .artist,.u4ie-on .creator,.u4ie-on .composer{'
    + 'outline:2px dashed #37a86e;outline-offset:4px;border-radius:4px;cursor:text}'
    + '.u4ie-on .album-card li,.u4ie-on .entries li{outline:1px dashed rgba(55,168,110,.55);outline-offset:2px;border-radius:4px}';

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }

  var panel = null, usage = [], dirty = false;

  function setMsg(t, ok) {
    if (!panel) return;
    var m = panel.querySelector('.u4ie-msg');
    m.textContent = t; m.className = 'u4ie-msg ' + (ok ? 'ok' : 'err');
  }

  function sbPost(row) {
    var s = sbSession();
    var h = { apikey: SB_KEY, 'Content-Type': 'application/json', Prefer: 'return=representation' };
    if (s) h.Authorization = 'Bearer ' + s.access_token;
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
    if (!isOwner()) return Promise.reject(new Error('這個帳號沒有編輯權限（請用站主帳號登入）'));
    return sbPost({ kind: kind, rel: relPath(), payload: payload, status: 'pending',
                    requested_by: email(), created_at: new Date().toISOString() });
  }

  function renderUsage() {
    var box = panel.querySelector('.u4ie-uses');
    box.innerHTML = '';
    panel.querySelector('.u4ie-n').textContent = '（' + usage.length + ' 筆）';
    usage.forEach(function (u, i) {
      var w = el('div', 'u4ie-use');
      w.innerHTML = '<label>作品標題（連結文字）</label>'
        + '<input type="text" data-i="' + i + '" data-f="title">'
        + '<label>連結網址（單集網址）</label>'
        + '<input type="text" data-i="' + i + '" data-f="href">'
        + '<label>括號標記（可留空）</label>'
        + '<input type="text" data-i="' + i + '" data-f="label">'
        + '<div class="u4ie-row"><button type="button" class="u4ie-del" data-del="' + i + '">刪除這筆</button></div>';
      w.querySelectorAll('input').forEach(function (inp) {
        inp.value = u[inp.dataset.f] || '';
        inp.addEventListener('input', function () {
          usage[+inp.dataset.i][inp.dataset.f] = inp.value;
          dirty = true;
        });
      });
      w.querySelector('[data-del]').addEventListener('click', function () {
        usage.splice(+this.dataset.del, 1); dirty = true; renderUsage();
      });
      box.appendChild(w);
    });
  }

  function buildPanel() {
    var p = el('div', 'u4ie-panel');

    var hd = el('div', 'u4ie-hd');
    hd.appendChild(el('b', null, '✏️ 就地編輯'));
    var x = el('button', 'u4ie-x', '✕'); x.type = 'button';
    x.title = '關閉（不儲存）';
    x.onclick = function () {
      if (dirty && !confirm('有還沒存的修改，確定關閉？')) return;
      document.body.classList.remove('u4ie-on');
      p.remove(); panel = null; dirty = false;
    };
    hd.appendChild(x);
    p.appendChild(hd);

    var bd = el('div', 'u4ie-bd');

    var st = el('div', 'u4ie-sec');
    st.innerHTML = '<label>曲名</label><input type="text" data-k="title">'
                 + '<label>作者</label><input type="text" data-k="artist">'
                 + '<div class="u4ie-row"><button type="button" class="u4ie-ghost" data-act="saveTitle">只存曲名／作者</button></div>';
    bd.appendChild(st);

    var us = el('div', 'u4ie-sec');
    us.innerHTML = '<label style="margin-top:14px;font-size:13.5px;color:#334">使用作品 <span class="u4ie-n"></span></label>'
                 + '<div class="u4ie-uses"></div>'
                 + '<div class="u4ie-row"><button type="button" class="u4ie-ghost" data-act="add">＋ 加一筆使用作品</button></div>';
    bd.appendChild(us);

    var mk = el('div', 'u4ie-sec');
    mk.innerHTML = '<div class="u4ie-row"><label style="display:inline-flex;gap:8px;align-items:center;margin:0;font-size:14px;color:#1f2733">'
                 + '<input type="checkbox" class="u4ie-mark" style="width:20px;height:20px"> 專輯頁這首打勾（有使用作品）</label></div>'
                 + '<div class="u4ie-row"><button type="button" class="u4ie-ghost" data-act="saveMark">只存 ✓ 狀態</button></div>';
    bd.appendChild(mk);

    var row = el('div', 'u4ie-row');
    var go = el('button', 'u4ie-go', '💾 儲存並上線');
    go.type = 'button';
    go.onclick = doSaveAll;
    row.appendChild(go);
    bd.appendChild(row);

    var m = el('div', 'u4ie-msg'); bd.appendChild(m);
    bd.appendChild(el('div', 'u4ie-hint',
      '存一次就是一個版本。送出後約 1–3 分鐘官網更新；改壞了跟我說，可以退回上一版。'));

    p.appendChild(bd);
    document.body.appendChild(p);
    panel = p;

    p.querySelector('[data-k=title]').value = pickText();
    p.querySelector('[data-k=artist]').value = pickArtist();
    usage = pickUsage();
    p.querySelector('.u4ie-mark').checked = usage.length > 0;
    renderUsage();

    p.querySelector('[data-k=title]').addEventListener('input', function () { dirty = true; });
    p.querySelector('[data-k=artist]').addEventListener('input', function () { dirty = true; });
    p.querySelector('.u4ie-mark').addEventListener('change', function () { dirty = true; });

    p.querySelector('[data-act=add]').onclick = function () {
      usage.push({ href: '', title: '', label: '' }); dirty = true; renderUsage();
      var all = panel.querySelectorAll('.u4ie-use');
      if (all.length) all[all.length - 1].querySelector('input').focus();
    };
    p.querySelector('[data-act=saveTitle]').onclick = async function () {
      try {
        var d = await submit('save_title', {
          title: panel.querySelector('[data-k=title]').value.trim(),
          artist: panel.querySelector('[data-k=artist]').value.trim()
        });
        setMsg('✅ 曲名／作者已送出（# ' + (d.id || '?') + '），約 1–3 分鐘上線。', true);
      } catch (e) { setMsg('送出失敗：' + e.message, false); }
    };
    p.querySelector('[data-act=saveMark]').onclick = async function () {
      try {
        var d = await submit('save_mark', { checked: panel.querySelector('.u4ie-mark').checked });
        setMsg('✅ ✓ 狀態已送出（# ' + (d.id || '?') + '），約 1–3 分鐘上線。', true);
      } catch (e) { setMsg('送出失敗：' + e.message, false); }
    };

    var titleInp = p.querySelector('[data-k=title]');
    if (titleInp) setTimeout(function () { titleInp.focus(); }, 80);
  }

  async function doSaveAll() {
    var go = panel.querySelector('.u4ie-go');
    var title = panel.querySelector('[data-k=title]').value.trim();
    var artist = panel.querySelector('[data-k=artist]').value.trim();
    var items = usage.filter(function (u) { return (u.href || '').trim() && (u.title || '').trim(); });
    if (items.length !== usage.length) {
      if (!confirm('有 ' + (usage.length - items.length) + ' 筆沒填連結或標題，會略過。要繼續嗎？')) return;
    }
    go.disabled = true; go.textContent = '送出中…';
    var sent = 0;
    try {
      await submit('save_title', { title: title, artist: artist }); sent++;
      await submit('save_usage', { items: items }); sent++;
      await submit('save_mark', { checked: panel.querySelector('.u4ie-mark').checked }); sent++;
      dirty = false;
      setMsg('✅ 已送出 ' + sent + ' 項修改，約 1–3 分鐘官網更新（重新整理可看結果）。', true);
    } catch (e) {
      setMsg('送出失敗（已成功 ' + sent + ' 項）：' + e.message, false);
    } finally {
      go.disabled = false; go.textContent = '💾 儲存並上線';
    }
  }

  /* 2026-11-27：站主沒登入時，不再「整個消失」→ 顯示一顆淡色提示，點下去去登入 */
  function showLoginHint() {
    if (document.querySelector('.u4ie-login')) return;
    var a = el('a', 'u4ie-login', '🔑 站主登入後可編輯');
    a.href = '/music-library/login.html';
    a.title = '用站主帳號登入後，右上角會出現 ✏️ 就地編輯';
    document.body.appendChild(a);
  }

  function addButton() {
    if (document.querySelector('.u4ie-btn')) return;
    if (!isOwner()) { showLoginHint(); return; }
    var b = el('button', 'u4ie-btn', '✏️');
    b.type = 'button';
    b.title = '就地編輯這一頁（站主）';
    b.onclick = function () {
      if (panel) {
        if (dirty && !confirm('有還沒存的修改，確定關閉？')) return;
        document.body.classList.remove('u4ie-on');
        panel.remove(); panel = null; dirty = false;
        return;
      }
      document.body.classList.add('u4ie-on');
      buildPanel();
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
      window.__u4ieState = { email: email() || '(未登入)', isOwner: isOwner(), btn: !!document.querySelector('.u4ie-btn') };
      console.info('[u4-inline] boot email=', window.__u4ieState.email, 'isOwner=', window.__u4ieState.isOwner);
    } catch (e) {}
    addButton();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
  [400, 1200, 2500].forEach(function (t) { setTimeout(boot, t); });
  window.addEventListener('focus', boot);
})();
