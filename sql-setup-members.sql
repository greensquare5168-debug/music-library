-- ============================================================
-- 站主看「會員名單」用的設定（在 Supabase → SQL Editor 貼上執行一次）
-- 作用：每次有人註冊，自動寫進 profiles 表；只有站主能讀全部。
-- ============================================================

-- 1) 會員資料表
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  name text,
  created_at timestamptz default now()
);

-- 2) 開 RLS（沒開的話任何人都能讀）
alter table public.profiles enable row level security;

-- 3) 權限：站主可讀全部；自己可讀/改自己那筆
drop policy if exists "owner read all" on public.profiles;
create policy "owner read all" on public.profiles
  for select to authenticated
  using ((auth.jwt() ->> 'email') = 'greensquare5168@gmail.com');

drop policy if exists "self read" on public.profiles;
create policy "self read" on public.profiles
  for select to authenticated
  using (id = auth.uid());

drop policy if exists "self update" on public.profiles;
create policy "self update" on public.profiles
  for update to authenticated
  using (id = auth.uid());

-- 4) 新註冊自動建立 profile（含名字）
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (id, email, name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- 5) 把「已經註冊過的人」補進來（含之前測試帳號）
insert into public.profiles (id, email, name)
select id, email, coalesce(raw_user_meta_data->>'name', split_part(email, '@', 1))
from auth.users
on conflict (id) do nothing;
