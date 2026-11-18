/* ============================================================
   後端設定（Supabase）—— 只要填這兩行，全站登入就會變成「真的」
   1) 到 https://supabase.com 註冊（免費）→ New project
   2) 專案 → Settings → API：
        Project URL         → 填到 SUPABASE_URL
        anon / publishable  → 填到 SUPABASE_ANON_KEY
   3) Authentication → Providers → Email：可關掉 "Confirm email" 方便測試

   ⚠️ 這個檔案會公開在網路上，只准放 anon/publishable key。
      service_role key（有 * 號那個）絕對不可以放進來。
   ============================================================ */
window.SUPABASE_URL = '';        // 例：https://abcdefghijkl.supabase.co
window.SUPABASE_ANON_KEY = '';   // 例：sb_publishable_xxx 或 eyJhbGciOiJIUzI1NiIs...
