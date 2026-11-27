<!-- 貼在 _admin/supabase_site_edits.sql 的最後面，再按 Run -->
grant select, insert on public.site_edits to authenticated;
grant usage, select on sequence public.site_edits_id_seq to authenticated;
