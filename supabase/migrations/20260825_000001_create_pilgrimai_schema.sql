-- PilgrimAI initial Supabase schema
--
-- The current NestJS application uses SUPABASE_SERVICE_ROLE_KEY to upsert
-- Google profiles. The service role bypasses RLS; browser clients do not use
-- Supabase directly. Therefore profile and conversation data stays private by
-- default, while active reference data is publicly readable.

create extension if not exists pgcrypto;

create or replace function public.set_pilgrimai_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table public.profiles (
  id uuid primary key default gen_random_uuid(),
  google_id text not null unique,
  email text not null unique,
  full_name text not null,
  avatar_url text,
  preferred_language text not null default 'en'
    check (preferred_language in ('en', 'te', 'hi')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.temples (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  full_name text,
  district text,
  state text not null default 'Telangana',
  address text,
  latitude numeric(9, 6),
  longitude numeric(9, 6),
  google_maps_url text,
  official_website text,
  contact_numbers jsonb not null default '[]'::jsonb,
  facilities jsonb not null default '[]'::jsonb,
  image_url text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint temples_coordinates_check check (
    (latitude is null and longitude is null)
    or (latitude between -90 and 90 and longitude between -180 and 180)
  )
);

create table public.hotels (
  id uuid primary key default gen_random_uuid(),
  external_id text unique,
  temple_id uuid not null references public.temples(id) on delete restrict,
  name text not null,
  hotel_type text,
  address text,
  distance_from_temple_km numeric(7, 2),
  price_category text,
  price_min numeric(10, 2),
  price_max numeric(10, 2),
  rating numeric(2, 1) check (rating is null or rating between 0 and 5),
  contact_numbers jsonb not null default '[]'::jsonb,
  amenities jsonb not null default '[]'::jsonb,
  booking_urls jsonb not null default '[]'::jsonb,
  image_url text,
  description text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint hotels_price_range_check check (
    price_min is null or price_max is null or price_min <= price_max
  ),
  constraint hotels_distance_check check (
    distance_from_temple_km is null or distance_from_temple_km >= 0
  )
);

create table public.darshan (
  id uuid primary key default gen_random_uuid(),
  temple_id uuid not null references public.temples(id) on delete restrict,
  name text not null,
  description text,
  darshan_type text not null default 'general',
  price numeric(10, 2) check (price is null or price >= 0),
  duration_minutes integer check (duration_minutes is null or duration_minutes > 0),
  booking_url text,
  schedule jsonb not null default '{}'::jsonb,
  eligibility jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.rituals (
  id uuid primary key default gen_random_uuid(),
  temple_id uuid not null references public.temples(id) on delete restrict,
  name text not null,
  description text,
  ritual_type text,
  price numeric(10, 2) check (price is null or price >= 0),
  duration_minutes integer check (duration_minutes is null or duration_minutes > 0),
  booking_url text,
  schedule jsonb not null default '{}'::jsonb,
  requirements jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.conversations (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.profiles(id) on delete cascade,
  temple_id uuid references public.temples(id) on delete set null,
  title text,
  language text not null default 'en' check (language in ('en', 'te', 'hi')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null check (char_length(content) between 1 and 20000),
  agent_used text,
  source_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index hotels_temple_id_idx on public.hotels(temple_id);
create index hotels_price_category_idx on public.hotels(price_category);
create index hotels_rating_idx on public.hotels(rating desc nulls last);
create index hotels_amenities_gin_idx on public.hotels using gin(amenities);
create index darshan_temple_id_active_idx on public.darshan(temple_id, is_active)
  where is_active = true;
create index rituals_temple_id_active_idx on public.rituals(temple_id, is_active)
  where is_active = true;
create index conversations_temple_id_idx on public.conversations(temple_id);
create index conversations_profile_updated_at_idx on public.conversations(profile_id, updated_at desc);
create index messages_conversation_created_at_idx on public.messages(conversation_id, created_at);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_pilgrimai_updated_at();

create trigger temples_set_updated_at
before update on public.temples
for each row execute function public.set_pilgrimai_updated_at();

create trigger hotels_set_updated_at
before update on public.hotels
for each row execute function public.set_pilgrimai_updated_at();

create trigger darshan_set_updated_at
before update on public.darshan
for each row execute function public.set_pilgrimai_updated_at();

create trigger rituals_set_updated_at
before update on public.rituals
for each row execute function public.set_pilgrimai_updated_at();

create trigger conversations_set_updated_at
before update on public.conversations
for each row execute function public.set_pilgrimai_updated_at();

alter table public.profiles enable row level security;
alter table public.temples enable row level security;
alter table public.hotels enable row level security;
alter table public.darshan enable row level security;
alter table public.rituals enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

-- Reference data is safe to display in the public PilgrimAI directory while active.
create policy "Public can read temples"
on public.temples for select to anon, authenticated using (true);

create policy "Public can read hotels"
on public.hotels for select to anon, authenticated using (true);

create policy "Public can read darshan"
on public.darshan for select to anon, authenticated using (is_active = true);

create policy "Public can read rituals"
on public.rituals for select to anon, authenticated using (is_active = true);

-- The application uses a custom NestJS session rather than Supabase Auth, so
-- auth.uid() cannot safely identify a profile. Keep private data explicitly
-- denied to browser roles; the service role bypasses these policies.
create policy "Browser cannot read profiles"
on public.profiles for select to anon, authenticated using (false);

create policy "Browser cannot read conversations"
on public.conversations for select to anon, authenticated using (false);

create policy "Browser cannot read messages"
on public.messages for select to anon, authenticated using (false);

grant select on public.temples, public.hotels, public.darshan, public.rituals to anon, authenticated;
