/* ============================================================
   角色判斷：站主（owner）／瀏覽（viewer）
   - 站主名單寫在這裡（Email）
   - ⚠️ 這是「介面」層的區分，只決定看到什麼；
     真正不能給人看的資料，要在 Supabase 用 RLS 鎖（見 admin.html 說明）
   ============================================================ */
export const OWNER_EMAILS = [
  'greensquare5168@gmail.com'
];

export const ROLE_TEXT = { owner: '站主模式', viewer: '瀏覽模式' };

export function roleOf(session) {
  const email = ((session && session.user && session.user.email) || '').toLowerCase();
  return OWNER_EMAILS.includes(email) ? 'owner' : 'viewer';
}

export function displayName(session) {
  const u = (session && session.user) || {};
  return (u.user_metadata && u.user_metadata.name) || u.email || '會員';
}
