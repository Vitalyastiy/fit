-- Таблица тренировок
create table workouts (
  id bigint generated always as identity primary key,
  date text not null,
  entries jsonb not null,
  created_at timestamptz default now()
);

-- Включаем Row Level Security (обязательно для доступа через публичный API)
alter table workouts enable row level security;

-- Разрешаем анонимному ключу (anon) читать, добавлять и удалять записи.
-- Это подходит для личного дневника тренировок без чувствительных данных.
-- Кто угодно с URL и anon-ключом сможет обращаться к этой таблице,
-- поэтому не храни тут ничего, что не должно быть публично доступно.
create policy "allow all for anon" on workouts
  for all
  to anon
  using (true)
  with check (true);
