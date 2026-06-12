create extension if not exists supabase_vault with schema vault;

create or replace function public.get_app_secret(secret_name text)
returns text
language sql
security definer
set search_path = public, vault
as $$
  select decrypted_secret
  from vault.decrypted_secrets
  where name = secret_name
  limit 1;
$$;

create table if not exists user_profile (
  user_id uuid primary key default gen_random_uuid(),
  nickname text,
  goal text not null,
  allergies text[] default '{}',
  disliked_foods text[] default '{}',
  preferred_foods text[] default '{}',
  budget_level text not null,
  cook_type text not null,
  updated_at timestamp default now()
);

alter table user_profile enable row level security;

create table if not exists meal_record (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  meal_type text not null,
  image_url text not null,
  description text,
  foods jsonb,
  nutrition_result jsonb,
  health_score int,
  risk_tags text[] default '{}',
  next_meal_advice text,
  status text default '待分析',
  eaten_at timestamp default now(),
  created_at timestamp default now()
);

alter table meal_record enable row level security;

create index if not exists meal_record_user_eaten_at_idx
on meal_record (user_id, eaten_at desc);

create table if not exists weekly_report (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  week_start date not null,
  week_end date not null,
  summary text not null,
  completeness text,
  average_score int,
  frequent_risks text[] default '{}',
  nutrition_lack text[] default '{}',
  risk_analysis text,
  compensation_plan text[] default '{}',
  note text,
  created_at timestamp default now(),
  unique(user_id, week_start)
);

alter table weekly_report enable row level security;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'meal-images',
  'meal-images',
  false,
  1500000,
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do update
set
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
