create table if not exists public.admin_adjustments (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),

  admin_user_id uuid not null,
  target_user_id uuid not null,

  action text not null check (action in ('ADD_COINS', 'SUB_COINS', 'ADD_TRIAL', 'SUB_TRIAL')),
  delta integer not null,

  reason text null,
  request_id text null,
  ip text null,
  user_agent text null
);

create index if not exists admin_adjustments_target_idx
  on public.admin_adjustments(target_user_id, created_at desc);
create index if not exists admin_adjustments_admin_idx
  on public.admin_adjustments(admin_user_id, created_at desc);

alter table public.admin_adjustments enable row level security;

create policy "No access by default" on public.admin_adjustments
for all using (false);

create policy "Admins can read audit logs" on public.admin_adjustments
for select
using (
  exists (
    select 1 from public.profiles p
    where p.user_id = auth.uid()
      and p.role_user = 'admin'
  )
);

create policy "Admins can insert audit logs" on public.admin_adjustments
for insert
with check (
  exists (
    select 1 from public.profiles p
    where p.user_id = auth.uid()
      and p.role_user = 'admin'
  )
);
