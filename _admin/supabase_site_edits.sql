-- 站主就地編輯｜Supabase 資料表 + RLS（2026-11-27，孝瓏「直接在頁上編輯」）
-- 用法：Supabase 後台 → SQL Editor → 貼上整段 → Run（一次就好）

create table if not exists public.site_edits (
  id           bigserial primary key,
  kind         text not null check (kind in ('save_title','save_usage','save_mark')),
  rel          text not null,
  payload      jsonb not null default '{}'::jsonb,
  status       text not null default 'pending'
               check (status in ('pending','applying','done','error')),
  requested_by text,
  commit       text,
  note         text,
  created_at   timestamptz not null default now(),
  picked_at    timestamptz,
  done_at      timestamptz
);

create index if not exists site_edits_status_idx on public.site_edits (status, created_at);
create index if not exists site_edits_rel_idx    on public.site_edits (rel);

alter table public.site_edits enable row level security;

-- 只有站主帳號可以提出編輯（且只能是 pending、只能是那三種動作）
drop policy if exists site_edits_owner_insert on public.site_edits;
create policy site_edits_owner_insert on public.site_edits
  for insert to authenticated
  with check (
    lower(coalesce(auth.jwt() ->> 'email','')) in ('linxiaolong0395@gmail.com')
    and status = 'pending'
    and kind in ('save_title','save_usage','save_mark')
  );

-- 站主只看得到自己提出的
drop policy if exists site_edits_owner_select on public.site_edits;
create policy site_edits_owner_select on public.site_edits
  for select to authenticated
  using (lower(coalesce(requested_by,'')) = lower(coalesce(auth.jwt() ->> 'email','')));

-- 一般人（甚至未登入）不能讀寫；狀態更新只給 service_role（RLS 不開 update/delete policy）

grant select, insert on public.site_edits to authenticated;
grant usage, select on sequence public.site_edits_id_seq to authenticated;
