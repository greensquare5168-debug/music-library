/* ============================================================
   站主聊天框（只有站主登入後才出現）
   - 沒登入 / 非站主 → 什麼都不做（連載入都不載）
   - 金鑰不在這裡：真正的 Gemini key 在 Supabase Edge Function 的環境變數
   - 後端會再驗一次身分（改網頁也騙不過）
   ============================================================ */
const SUPA_URL = 'https://lgsijyfahyoceicqehwf.supabase.co';
const SUPA_KEY = 'sb_publishable_O_se8emP48TwCIZ3e79Hrw_0e6Y0s4D';
const OWNER_EMAILS = ['greensquare5168@gmail.com'];
const FN_URL = SUPA_URL + '/functions/v1/site-chat';

/* ---------- 1) 有登入紀錄才繼續 ---------- */
function hasAuthToken() {
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i) || '';
      if (k.startsWith('sb-') && k.endsWith('-auth-token')) return true;
    }
  } catch (e) {}
  return false;
}
if (!hasAuthToken()) throw new Error('no session');

/* ---------- 2) 拿 session、確認是站主 ---------- */
const { createClient } = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm');
const sb = createClient(SUPA_URL, SUPA_KEY, { auth: { persistSession: true, autoRefreshToken: true } });
const { data: sd } = await sb.auth.getSession();
const session = sd && sd.session;
const email = String((session && session.user && session.user.email) || '').toLowerCase();
if (!session || !OWNER_EMAILS.includes(email)) throw new Error('not owner');

/* ---------- 3) 樣式 ---------- */
const css = `
#u4chat-btn{position:fixed;right:20px;bottom:20px;width:56px;height:56px;border-radius:50%;border:0;cursor:pointer;
 background:linear-gradient(135deg,#2f6feb,#1e4fb8);color:#fff;font-size:24px;line-height:1;box-shadow:0 8px 24px rgba(20,40,90,.28);
 z-index:9998;display:flex;align-items:center;justify-content:center;transition:transform .12s}
#u4chat-btn:hover{transform:translateY(-2px)}
#u4chat-panel{position:fixed;right:20px;bottom:88px;width:360px;max-width:calc(100vw - 24px);height:min(520px,calc(100vh - 120px));
 background:#fff;border:1px solid #e3e8ee;border-radius:16px;box-shadow:0 18px 48px rgba(20,40,70,.22);
 z-index:9999;display:none;flex-direction:column;overflow:hidden;font-family:inherit}
#u4chat-panel.on{display:flex}
.u4c-head{display:flex;align-items:center;gap:8px;padding:12px 14px;background:#f8fafc;border-bottom:1px solid #e8edf3}
.u4c-head b{font-size:14px;color:#1f2733}
.u4c-chip{font-size:11px;color:#b45309;background:#fff7e6;border:1px solid #f3d9a4;border-radius:999px;padding:1px 8px}
.u4c-head .u4c-x{margin-left:auto;display:flex;gap:4px}
.u4c-head button{border:0;background:transparent;color:#8a97a8;font-size:16px;cursor:pointer;padding:4px 6px;border-radius:6px;font:inherit}
.u4c-head button:hover{background:#eef2f7;color:#334}
.u4c-body{flex:1;overflow-y:auto;padding:14px;background:#fbfcfe;display:flex;flex-direction:column;gap:10px}
.u4c-m{max-width:86%;padding:9px 12px;border-radius:12px;font-size:14px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.u4c-m.me{align-self:flex-end;background:#2f6feb;color:#fff;border-bottom-right-radius:4px}
.u4c-m.ai{align-self:flex-start;background:#fff;border:1px solid #e3e8ee;color:#1f2733;border-bottom-left-radius:4px}
.u4c-m.err{align-self:flex-start;background:#fff1f0;border:1px solid #f6c2bd;color:#a4262c}
.u4c-dots{align-self:flex-start;color:#98a4b4;font-size:18px;letter-spacing:2px;padding:2px 6px}
.u4c-foot{border-top:1px solid #e8edf3;padding:10px;display:flex;gap:8px;background:#fff}
.u4c-foot textarea{flex:1;resize:none;border:1px solid #cfd8e3;border-radius:10px;padding:9px 11px;font:inherit;font-size:14px;
 line-height:1.4;max-height:96px;outline:none;color:#1f2733}
.u4c-foot textarea:focus{border-color:#2f6feb;box-shadow:0 0 0 3px rgba(47,111,235,.12)}
.u4c-send{border:0;border-radius:10px;background:#2f6feb;color:#fff;font:inherit;font-size:15px;font-weight:700;padding:0 14px;cursor:pointer}
.u4c-send:disabled{background:#9db4dd;cursor:not-allowed}
.u4c-hint{font-size:11px;color:#9aa6b6;text-align:center;padding:0 14px 8px;background:#fff}
@media(max-width:480px){#u4chat-panel{right:8px;left:8px;width:auto;bottom:84px;height:min(70vh,520px)}}
`;

const style = document.createElement('style');
style.textContent = css;
document.head.appendChild(style);

/* ---------- 4) 版面 ---------- */
const root = document.createElement('div');
root.innerHTML = `
  <button id="u4chat-btn" title="跟 U4 說要改什麼">💬</button>
  <div id="u4chat-panel">
    <div class="u4c-head">
      <b>U4 助手</b><span class="u4c-chip">站主</span>
      <div class="u4c-x">
        <button id="u4c-clear" title="清除對話">🗑</button>
        <button id="u4c-close" title="收起">✕</button>
      </div>
    </div>
    <div class="u4c-body" id="u4c-body"></div>
    <div class="u4c-foot">
      <textarea id="u4c-in" rows="1" placeholder="要改什麼？例：BR-183 那首作者錯了"></textarea>
      <button class="u4c-send" id="u4c-send">送出</button>
    </div>
    <div class="u4c-hint">這個框幫你想「怎麼改」；實際修改請在 Discord 跟 U4 說</div>
  </div>`;
document.body.appendChild(root);

const btn = document.getElementById('u4chat-btn');
const panel = document.getElementById('u4chat-panel');
const bodyEl = document.getElementById('u4c-body');
const inp = document.getElementById('u4c-in');
const sendBtn = document.getElementById('u4c-send');
const STORE = 'u4chat-msgs-v1';

let msgs = [];
try { msgs = JSON.parse(sessionStorage.getItem(STORE) || '[]'); } catch (e) { msgs = []; }
if (!msgs.length) {
  msgs = [{ role: 'model', text: '我是 U4。你在哪一頁、想改什麼，直接跟我說（例：這頁作者名字錯了、這首要標記使用作品）。' }];
}

function save() { try { sessionStorage.setItem(STORE, JSON.stringify(msgs.slice(-20))); } catch (e) {} }

function bubble(m) {
  const d = document.createElement('div');
  d.className = 'u4c-m ' + (m.role === 'user' ? 'me' : (m.role === 'error' ? 'err' : 'ai'));
  d.textContent = m.text;
  bodyEl.appendChild(d);
}

function render() {
  bodyEl.innerHTML = '';
  msgs.forEach(bubble);
  bodyEl.scrollTop = bodyEl.scrollHeight;
}
render();

function open(v) {
  panel.classList.toggle('on', v);
  if (v) { setTimeout(() => inp.focus(), 60); bodyEl.scrollTop = bodyEl.scrollHeight; }
}
btn.addEventListener('click', () => open(!panel.classList.contains('on')));
document.getElementById('u4c-close').addEventListener('click', () => open(false));
document.getElementById('u4c-clear').addEventListener('click', () => {
  msgs = [{ role: 'model', text: '對話清掉了，重新說吧。' }];
  save(); render();
});

inp.addEventListener('input', () => {
  inp.style.height = 'auto';
  inp.style.height = Math.min(inp.scrollHeight, 96) + 'px';
});
inp.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
sendBtn.addEventListener('click', send);

async function send() {
  const text = inp.value.trim();
  if (!text || sendBtn.disabled) return;
  inp.value = '';
  inp.style.height = 'auto';
  msgs.push({ role: 'user', text });
  save(); render();

  sendBtn.disabled = true;
  const dots = document.createElement('div');
  dots.className = 'u4c-dots';
  dots.textContent = '•••';
  bodyEl.appendChild(dots);
  bodyEl.scrollTop = bodyEl.scrollHeight;

  try {
    const hist = msgs.filter((m) => m.role === 'user' || m.role === 'model').slice(-12);
    const { data: fresh } = await sb.auth.getSession();
    const token = fresh && fresh.session && fresh.session.access_token;
    const res = await fetch(FN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: SUPA_KEY,
        Authorization: 'Bearer ' + (token || ''),
      },
      body: JSON.stringify({ messages: hist, page: location.pathname + ' ｜ ' + document.title }),
    });
    const j = await res.json().catch(() => ({}));
    dots.remove();
    if (!res.ok) {
      msgs.push({ role: 'error', text: j.error || ('發生錯誤（' + res.status + '）') });
    } else {
      msgs.push({ role: 'model', text: j.reply || '（沒有回覆）' });
    }
  } catch (e) {
    dots.remove();
    msgs.push({ role: 'error', text: '連不上後端：' + (e.message || e) });
  }
  save(); render();
  sendBtn.disabled = false;
  inp.focus();
}
