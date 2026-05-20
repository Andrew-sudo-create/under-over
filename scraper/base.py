from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(slots=True)
class RawListing:
    source: str
    listing_url: str
    source_listing_id: str | None
    payload: dict[str, Any]
    scraped_at: datetime


@dataclass(slots=True)
class NormalizedListing:
    listing_url: str
    source: str
    city: str | None = None
    suburb: str | None = None
    property_type: str | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    parking_spaces: int | None = None
    floor_area_sqm: float | None = None
    land_area_sqm: float | None = None
    asking_price: float | None = None
    listed_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class ListingAdapter(Protocol):
    source_name: str

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        """Return listing detail URLs discovered from a search page."""

    def fetch_listing(self, listing_url: str) -> RawListing:
        """Fetch raw listing information from source."""

    def normalize_listing(self, raw: RawListing) -> NormalizedListing:
        """Map raw listing payload to normalized listing shape."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
