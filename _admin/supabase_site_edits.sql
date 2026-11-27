-- 站主編輯器雲端中繼｜Supabase 資料表（2026-11-27）
-- 在 Supabase 後台 → SQL Editor 貼上整段執行（一次就好）

create table if not exists public.site_edits (
  id           bigserial primary key,
  kind         text not null check (kind in ('save_title','save_usage','save_mark')),
  rel          text not null,                                  -- 例：罐頭音樂研究所/…/index.html
  payload      jsonb not null default '{}'::jsonb,
  status       text not null default 'pending'                 -- pending / done / error
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

-- 只有站主帳號（已登入、且信箱在名單內）可以「提出」編輯
drop policy if exists site_edits_owner_insert on public.site_edits;
create policy site_edits_owner_insert on public.site_edits
  for insert to authenticated
  with check (
    lower(coalesce(auth.jwt() ->> 'email','')) in ('linxiaolong0395@gmail.com')
    and status = 'pending'
    and kind in ('save_title','save_usage','save_mark')
  );

-- 站主只能看自己提出的
drop policy if exists site_edits_owner_select on public.site_edits;
create policy site_edits_owner_select on public.site_edits
  for select to authenticated
  using (lower(coalesce(auth.jwt() ->> 'email','')) = lower(coalesce(requested_by,'')));

-- 站主不能改狀態（只給 U4 的 service_role 用；RLS 不開 update/delete policy → 前端改不動）
