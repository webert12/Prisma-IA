-- Prisma IA v8: execute todo este arquivo no SQL Editor do Supabase.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  business_name text,
  business_type text,
  target_audience text,
  products_services text,
  whatsapp text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.generations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  tool_id text not null,
  input_data jsonb not null default '{}'::jsonb,
  output_text text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.financial_transactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  type text not null check (type in ('entrada','despesa')),
  description text not null check (char_length(description) between 1 and 140),
  category text not null default 'Outros',
  amount numeric(12,2) not null check (amount > 0),
  transaction_date date not null default current_date,
  note text,
  created_at timestamptz not null default now()
);
create index if not exists financial_transactions_user_date_idx on public.financial_transactions(user_id, transaction_date desc);

alter table public.profiles enable row level security;
alter table public.generations enable row level security;
alter table public.financial_transactions enable row level security;

drop policy if exists "Users can read own profile" on public.profiles;
drop policy if exists "Users can insert own profile" on public.profiles;
drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can read own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users can insert own profile" on public.profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id) with check (auth.uid() = id);

drop policy if exists "Users can read own generations" on public.generations;
drop policy if exists "Users can insert own generations" on public.generations;
drop policy if exists "Users can delete own generations" on public.generations;
create policy "Users can read own generations" on public.generations for select using (auth.uid() = user_id);
create policy "Users can insert own generations" on public.generations for insert with check (auth.uid() = user_id);
create policy "Users can delete own generations" on public.generations for delete using (auth.uid() = user_id);

drop policy if exists "Users manage own financial transactions" on public.financial_transactions;
create policy "Users manage own financial transactions" on public.financial_transactions for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
