-- Supabase / Postgres migration script (SQLite -> Supabase)
-- Paste into Supabase SQL Editor and Run

begin;

-- Optional: helpers for crypto / random UUID, etc.
create extension if not exists pgcrypto;

-- =========================
-- USERS
-- =========================
create table if not exists public.users (
  user_id    bigint primary key,
  username   text,
  first_name text,
  join_date  timestamptz not null default now()
);

-- =========================
-- FILES
-- =========================
create table if not exists public.files (
  file_id            text primary key,     -- e.g. file_3feb...
  file_path          text,
  file_name          text,
  user_id            bigint not null,
  created_at         timestamptz not null default now(),
  expires_at         timestamptz,
  storage_chat_id    bigint,
  storage_message_id bigint,

  -- requested metadata
  link_token         text,                 -- e.g. 3feb... (without file_)
  telegram_file_id   text,                 -- telegram media file_id
  media_title        text,                 -- video/file title
  random_key         text                  -- random column
);

-- =========================
-- CHANNELS
-- =========================
create table if not exists public.channels (
  channel_id       text primary key,
  channel_username text,
  added_by         bigint,
  added_at         timestamptz not null default now()
);

-- =========================
-- BROADCASTS
-- =========================
-- Note: No primary key added because your original structure didn't define one.
-- If you want, you can later add an id bigserial primary key.
create table if not exists public.broadcasts (
  message_id bigint,
  chat_id    bigint,
  sent_at    timestamptz not null default now(),
  expires_at timestamptz
);

-- =========================
-- INDEXES
-- =========================
create index if not exists idx_files_expires_at on public.files (expires_at);
create index if not exists idx_files_user_id on public.files (user_id);
create unique index if not exists idx_files_link_token_unique on public.files (link_token);

create index if not exists idx_broadcasts_expires_at on public.broadcasts (expires_at);

-- =========================
-- FOREIGN KEY (recommended)
-- =========================
do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'files_user_id_fkey'
  ) then
    alter table public.files
      add constraint files_user_id_fkey
      foreign key (user_id)
      references public.users(user_id)
      on delete cascade;
  end if;
end
$$;

commit;
