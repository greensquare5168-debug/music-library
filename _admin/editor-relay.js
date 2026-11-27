/* ===== 站主編輯器｜雲端中繼（2026-11-27）=====
   目的：孝瓏不必申請 GitHub token。
   - 她用網站會員（Supabase）登入 → 本站驗身分
   - 按「存檔」→ 改動寫進網站自己的資料庫（表 site_edits，狀態 pending）
   - U4 上的小程式每 2 分鐘取走 pending → 套進本機檔案 → git commit → push 上線
   - 只接受白名單信箱（OWNER_EMAILS）＋只接受三種動作（改曲名/作者、改使用作品、改✓）
   安全：瀏覽器拿不到 GitHub 權限；就算資料庫被塞垃圾，也只能動「那三種欄位」，
        且路徑一律由 U4 端 safe_page() 驗證必須落在 罐頭音樂研究所底下各 index.html
*/
(function () {
  var SB_URL = (window.SUPABASE_URL || '').trim();
  var SB_KEY = (window.SUPABASE_ANON_KEY || '').trim();
  var TABLE = 'site_edits';
  var OWNER_EMAILS = ['linxiaolong0395@gmail.com'];

  function sbSession() {
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i) || '';
        if (k.indexOf('sb-') === 0 && /-auth-token/.test(k)) {
          var o = JSON.parse(localStorage.getItem(k) || 'null');
          var s = o && (o.currentSession || o);
          if (s && s.access_token) return s;
        }
      }
    } catch (e) {}
    return null;
  }

  function session() { return sbSession(); }
  function email() {
    var s = sbSession();
    return s && s.user && s.user.email ? String(s.user.email).toLowerCase() : '';
  }
  function isOwner() { return OWNER_EMAILS.indexOf(email()) >= 0; }

  function api(path, opt) {
    opt = opt || {};
    var s = sbSession();
    var h = { apikey: SB_KEY, 'Content-Type': 'application/json', Prefer: 'return=representation' };
    if (s) h.Authorization = 'Bearer ' + s.access_token;
    return fetch(SB_URL.replace(/\/$/, '') + '/rest/v1/' + path, {
      method: opt.method || 'GET', headers: h, body: opt.body ? JSON.stringify(opt.body) : undefined
    }).then(function (r) {
      return r.text().then(function (t) {
        var d = {}; try { d = t ? JSON.parse(t) : {}; } catch (e) { d = { message: t }; }
        if (!r.ok) throw new Error((d.message || d.hint || ('HTTP ' + r.status)) + (d.code ? ' (' + d.code + ')' : ''));
        return d;
      });
    });
  }

  /* 送出一個編輯請求；resolve 回 {id, ...} */
  function submit(kind, rel, payload) {
    if (!isOwner()) return Promise.reject(new Error('這個帳號沒有編輯權限（請用站主帳號登入）'));
    var row = { kind: kind, rel: rel, payload: payload, status: 'pending',
                requested_by: email(), created_at: new Date().toISOString() };
    return api(TABLE, { method: 'POST', body: row }).then(function (d) {
      return (Array.isArray(d) ? d[0] : d) || {};
    });
  }

  /* 查某頁最近一次請求狀態（可選） */
  function latest(rel) {
    return api(TABLE + '?rel=eq.' + encodeURIComponent(rel) +
               '&order=created_at.desc&limit=3&select=id,kind,status,created_at,commit,note');
  }

  window.U4Edit = { session: session, email: email, isOwner: isOwner, submit: submit, latest: latest, OWNER_EMAILS: OWNER_EMAILS };
})();
