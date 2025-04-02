-- Enable RLS (Row Level Security)
alter table if exists public.users enable row level security;

-- Create tables with proper references and indexes

-- Users table (extends Supabase auth.users)
create table if not exists public.users (
    user_id uuid references auth.users primary key,
    email text not null unique,
    subscription_tier text not null default 'Free',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Market trends table
create table if not exists public.market_trends (
    id bigserial primary key,
    user_id uuid references public.users(user_id) not null,
    keyword text not null,
    trend_score float not null,
    data_collected_at timestamptz not null,
    created_at timestamptz not null default now()
);

-- Create index on data_collected_at for time-series queries
create index if not exists idx_market_trends_date on public.market_trends(data_collected_at desc);
create index if not exists idx_market_trends_user on public.market_trends(user_id, data_collected_at desc);

-- Competitors table
create table if not exists public.competitors (
    competitor_id bigserial primary key,
    user_id uuid references public.users(user_id) not null,
    name text not null,
    website text,
    created_at timestamptz not null default now(),
    unique(user_id, name)
);

-- Competitor activities table
create table if not exists public.competitor_activities (
    activity_id bigserial primary key,
    competitor_id bigint references public.competitors(competitor_id) not null,
    description text not null,
    detected_at timestamptz not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_competitor_activities_date 
on public.competitor_activities(detected_at desc);

-- Sentiments table
create table if not exists public.sentiments (
    sentiment_id bigserial primary key,
    user_id uuid references public.users(user_id) not null,
    keyword text not null,
    sentiment_score float not null,
    mention_count int not null default 1,
    data_collected_at timestamptz not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_sentiments_user_date 
on public.sentiments(user_id, data_collected_at desc);

-- Alerts table
create table if not exists public.alerts (
    alert_id bigserial primary key,
    user_id uuid references public.users(user_id) not null,
    alert_type text not null,
    message text not null,
    sent_at timestamptz not null default now(),
    is_read boolean not null default false
);

create index if not exists idx_alerts_user_date 
on public.alerts(user_id, sent_at desc);

-- RLS Policies

-- Users can only read their own data
create policy "Users can view own profile"
    on public.users for select
    using (auth.uid() = user_id);

-- Market Trends policies
create policy "Users can view own market trends"
    on public.market_trends for select
    using (auth.uid() = user_id);

create policy "Users can insert own market trends"
    on public.market_trends for insert
    with check (auth.uid() = user_id);

-- Competitors policies
create policy "Users can view own competitors"
    on public.competitors for select
    using (auth.uid() = user_id);

create policy "Users can manage own competitors"
    on public.competitors for all
    using (auth.uid() = user_id);

-- Competitor Activities policies
create policy "Users can view activities of their competitors"
    on public.competitor_activities for select
    using (exists (
        select 1 from public.competitors
        where competitor_id = public.competitor_activities.competitor_id
        and user_id = auth.uid()
    ));

-- Sentiments policies
create policy "Users can view own sentiment data"
    on public.sentiments for select
    using (auth.uid() = user_id);

create policy "Users can insert own sentiment data"
    on public.sentiments for insert
    with check (auth.uid() = user_id);

-- Alerts policies
create policy "Users can view own alerts"
    on public.alerts for select
    using (auth.uid() = user_id);

-- Enable RLS on all tables
alter table public.market_trends enable row level security;
alter table public.competitors enable row level security;
alter table public.competitor_activities enable row level security;
alter table public.sentiments enable row level security;
alter table public.alerts enable row level security;
