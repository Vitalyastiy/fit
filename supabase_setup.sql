-- Таблица тренировок в public (основная схема для supabase-js)
create table if not exists public.workouts (
  id bigint generated always as identity primary key,
  date text not null,
  entries jsonb not null,
  created_at timestamptz default now()
);

alter table public.workouts enable row level security;

drop policy if exists "allow all for anon" on public.workouts;
create policy "allow all for anon" on public.workouts
  for all
  to anon
  using (true)
  with check (true);

-- В этом проекте Data API по умолчанию смотрит схему `api`.
-- Дублируем таблицу туда, чтобы запросы без Accept-Profile тоже находили workouts.
create schema if not exists api;

create table if not exists api.workouts (
  id bigint generated always as identity primary key,
  date text not null,
  entries jsonb not null,
  created_at timestamptz default now()
);

alter table api.workouts enable row level security;

drop policy if exists "allow all for anon" on api.workouts;
create policy "allow all for anon" on api.workouts
  for all
  to anon
  using (true)
  with check (true);

-- Права для anon через PostgREST
grant usage on schema public to anon, authenticated;
grant usage on schema api to anon, authenticated;
grant select, insert, update, delete on public.workouts to anon, authenticated;
grant select, insert, update, delete on api.workouts to anon, authenticated;
