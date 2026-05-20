from __future__ import annotations

import json

import psycopg

from scraper.base import NormalizedListing, RawListing


def insert_raw_listing(cur: psycopg.Cursor, raw: RawListing) -> None:
    cur.execute(
        """
        insert into listings_raw (source, source_listing_id, listing_url, raw_payload, scraped_at)
        values (%s, %s, %s, %s::jsonb, %s)
        on conflict (listing_url)
        do update set
            source = excluded.source,
            source_listing_id = excluded.source_listing_id,
            raw_payload = excluded.raw_payload,
            scraped_at = excluded.scraped_at
        """,
        (raw.source, raw.source_listing_id, raw.listing_url, json.dumps(raw.payload), raw.scraped_at),
    )


def upsert_normalized_listing(cur: psycopg.Cursor, listing: NormalizedListing) -> None:
    cur.execute(
        """
        insert into listings_normalized (
            listing_url, source, city, suburb, property_type,
            bedrooms, bathrooms, parking_spaces, floor_area_sqm, land_area_sqm,
            asking_price, listed_at, first_seen_at, last_seen_at
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (listing_url)
        do update set
            source = excluded.source,
            city = excluded.city,
            suburb = excluded.suburb,
            property_type = excluded.property_type,
            bedrooms = excluded.bedrooms,
            bathrooms = excluded.bathrooms,
            parking_spaces = excluded.parking_spaces,
            floor_area_sqm = excluded.floor_area_sqm,
            land_area_sqm = excluded.land_area_sqm,
            asking_price = excluded.asking_price,
            listed_at = excluded.listed_at,
            last_seen_at = excluded.last_seen_at
        """,
        (
            listing.listing_url,
            listing.source,
            listing.city,
            listing.suburb,
            listing.property_type,
            listing.bedrooms,
            listing.bathrooms,
            listing.parking_spaces,
            listing.floor_area_sqm,
            listing.land_area_sqm,
            listing.asking_price,
            listing.listed_at,
            listing.first_seen_at,
            listing.last_seen_at,
        ),
    )


def insert_price_history(cur: psycopg.Cursor, listing: NormalizedListing) -> None:
    if listing.asking_price is None:
        return
    captured_at = listing.last_seen_at or listing.first_seen_at
    cur.execute(
        """
        insert into listing_price_history (listing_url, asking_price, captured_at)
        values (%s, %s, %s)
        """,
        (listing.listing_url, listing.asking_price, captured_at),
    )


def persist_listing(conn: psycopg.Connection, raw: RawListing, normalized: NormalizedListing) -> None:
    with conn.cursor() as cur:
        insert_raw_listing(cur, raw)
        upsert_normalized_listing(cur, normalized)
        insert_price_history(cur, normalized)
