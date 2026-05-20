from __future__ import annotations

from datetime import datetime
import json
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from scraper.base import ListingAdapter, NormalizedListing, RawListing, utcnow
from scraper.compliance import ComplianceGuard
from scraper.normalize import normalize_text, parse_float, parse_int


class Property24Adapter(ListingAdapter):
    source_name = "property24"

    def __init__(self, guard: ComplianceGuard | None = None) -> None:
        self.guard = guard or ComplianceGuard()

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        if not self.guard.can_fetch(search_url):
            raise PermissionError(f"robots.txt disallows scraping: {search_url}")

        self.guard.wait_with_jitter()
        with self.guard.build_client() as client:
            response = client.get(search_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        found: list[str] = []
        seen: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            if "/for-sale/" not in href and "/to-rent/" not in href:
                continue
            absolute = urljoin(search_url, href.split("?")[0].strip())
            if absolute in seen:
                continue
            if urlparse(absolute).netloc.endswith("property24.com"):
                seen.add(absolute)
                found.append(absolute)
            if len(found) >= limit:
                break

        return found

    def fetch_listing(self, listing_url: str) -> RawListing:
        if not self.guard.can_fetch(listing_url):
            raise PermissionError(f"robots.txt disallows scraping: {listing_url}")

        self.guard.wait_with_jitter()
        with self.guard.build_client() as client:
            response = client.get(listing_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        payload = self._extract_payload(soup)

        return RawListing(
            source=self.source_name,
            listing_url=listing_url,
            source_listing_id=payload.get("source_listing_id"),
            payload=payload,
            scraped_at=utcnow(),
        )

    def normalize_listing(self, raw: RawListing) -> NormalizedListing:
        payload = raw.payload
        return NormalizedListing(
            listing_url=raw.listing_url,
            source=raw.source,
            city=normalize_text(payload.get("city")),
            suburb=normalize_text(payload.get("suburb")),
            property_type=normalize_text(payload.get("property_type")),
            bedrooms=parse_int(payload.get("bedrooms")),
            bathrooms=parse_float(payload.get("bathrooms")),
            parking_spaces=parse_int(payload.get("parking_spaces")),
            floor_area_sqm=parse_float(payload.get("floor_area_sqm")),
            land_area_sqm=parse_float(payload.get("land_area_sqm")),
            asking_price=parse_float(payload.get("asking_price")),
            listed_at=self._parse_iso_datetime(payload.get("listed_at")),
            first_seen_at=raw.scraped_at,
            last_seen_at=raw.scraped_at,
        )

    def _extract_payload(self, soup: BeautifulSoup) -> dict[str, str]:
        payload: dict[str, str] = {}
        json_ld_script = soup.find("script", attrs={"type": "application/ld+json"})
        if json_ld_script and json_ld_script.string:
            try:
                data = json.loads(json_ld_script.string)
                if isinstance(data, list):
                    data = next((item for item in data if isinstance(item, dict)), {})
                if isinstance(data, dict):
                    payload["asking_price"] = str(data.get("offers", {}).get("price", "")).strip()
                    payload["property_type"] = str(data.get("@type", "")).strip()
                    payload["source_listing_id"] = str(data.get("identifier", "")).strip()
            except json.JSONDecodeError:
                pass

        title = soup.find("title")
        if title and title.text:
            payload["title"] = title.text.strip()

        return payload

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
