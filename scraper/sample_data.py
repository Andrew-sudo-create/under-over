from __future__ import annotations

from scraper.base import RawListing, utcnow


def sample_raw_listing() -> RawListing:
    now = utcnow()
    return RawListing(
        source="property24",
        listing_url="https://www.property24.com/for-sale/example-suburb/example-city/0000/123456789",
        source_listing_id="123456789",
        payload={
            "source_listing_id": "123456789",
            "city": "Johannesburg",
            "suburb": "Sandton",
            "property_type": "Apartment",
            "bedrooms": "2",
            "bathrooms": "1.5",
            "parking_spaces": "1",
            "floor_area_sqm": "89",
            "land_area_sqm": "89",
            "asking_price": "1,650,000",
            "listed_at": now.isoformat(),
        },
        scraped_at=now,
    )
