-- Einmalig im Supabase-Dashboard unter SQL Editor ausführen.
-- Legt die Tabelle an, in der /api/fortschritt die Lernstände ablegt.

create table if not exists public.fortschritt (
  app          text        not null,
  code         text        not null,
  daten        jsonb       not null,
  aktualisiert timestamptz not null default now(),
  primary key (app, code)
);

-- Zugriff nur über den Service-Role-Key der Serverless-Funktion: Row Level
-- Security an, aber keine Policy — damit kommt der öffentliche anon-Key nicht
-- an die Tabelle heran, der Service-Role-Key umgeht RLS ohnehin.
alter table public.fortschritt enable row level security;
