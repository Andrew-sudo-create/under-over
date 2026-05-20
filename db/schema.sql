-- under-over v1 initial schema

create table if not exists listings_raw (
    id bigserial primary key,
    source text not null,
    source_listing_id text,
    listing_url text not null unique,
    raw_payload jsonb not null,
    scraped_at timestamptz not null default now()
);

create table if not exists listings_normalized (
    id bigserial primary key,
    listing_url text not null unique,
    source text not null,
    city text,
    suburb text,
    property_type text,
    bedrooms int,
    bathrooms numeric(4, 2),
    parking_spaces int,
    floor_area_sqm numeric(10, 2),
    land_area_sqm numeric(10, 2),
    asking_price numeric(14, 2),
    listed_at timestamptz,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

create table if not exists listing_price_history (
    id bigserial primary key,
    listing_url text not null,
    asking_price numeric(14, 2) not null,
    captured_at timestamptz not null default now()
);

create index if not exists idx_listings_normalized_city_suburb
    on listings_normalized (city, suburb);

create index if not exists idx_listing_price_history_url_time
    on listing_price_history (listing_url, captured_at desc);
