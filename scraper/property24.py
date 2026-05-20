from __future__ import annotations

from datetime import datetime
import json
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from scraper.base import ListingAdapter, NormalizedListing, RawListing, utcnow
from scraper.compliance import ComplianceGuard
from scraper.normalize import normalize_text, parse_float, parse_int


class Property24Adapter(ListingAdapter):
    source_name = "property24"

    def __init__(self, guard: ComplianceGuard | None = None) -> None:
        self.guard = guard or ComplianceGuard()

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        with self.guard.build_client() as client:
            found: list[str] = []
            seen: set[str] = set()
            page = 1

            while len(found) < limit:
                paged_url = self._with_page(search_url, page)
                response = self.guard.get(client, paged_url)
                urls = self._extract_listing_urls(response.text, search_url)
                if not urls:
                    break

                newly_added = 0
                for absolute in urls:
                    if absolute in seen:
                        continue
                    seen.add(absolute)
                    found.append(absolute)
                    newly_added += 1
                    if len(found) >= limit:
                        break

                if newly_added == 0:
                    break
                page += 1
        return found

    def fetch_listing(self, listing_url: str) -> RawListing:
        with self.guard.build_client() as client:
            response = self.guard.get(client, listing_url)

        payload = self._extract_payload_from_html(response.text)

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

    def _extract_payload_from_html(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "html.parser")
        payload: dict[str, str] = {}

        json_ld_objects = self._extract_json_ld_objects(soup)
        listing_obj = self._pick_listing_object(json_ld_objects)
        if listing_obj:
            payload.update(self._payload_from_json_ld_listing(listing_obj))

        title = soup.find("title")
        if title and title.text:
            payload["title"] = title.text.strip()

        if "city" not in payload or "suburb" not in payload:
            city, suburb = self._extract_city_suburb_from_title(payload.get("title", ""))
            if city and "city" not in payload:
                payload["city"] = city
            if suburb and "suburb" not in payload:
                payload["suburb"] = suburb

        return payload

    def _extract_listing_urls(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            if "/for-sale/" not in href and "/to-rent/" not in href:
                continue
            absolute = urljoin(base_url, href.split("?")[0].strip())
            parsed = urlparse(absolute)
            if parsed.netloc.endswith("property24.com"):
                urls.append(absolute)
        return urls

    @staticmethod
    def _with_page(url: str, page: int) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query, keep_blank_values=True)
        query["Page"] = [str(page)]
        encoded = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=encoded))

    def _extract_json_ld_objects(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        objects: list[dict[str, Any]] = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue

            if isinstance(data, dict):
                objects.append(data)
            elif isinstance(data, list):
                objects.extend([item for item in data if isinstance(item, dict)])
        return objects

    @staticmethod
    def _pick_listing_object(objects: list[dict[str, Any]]) -> dict[str, Any] | None:
        preferred_types = {"Offer", "Product", "Residence", "SingleFamilyResidence", "Apartment", "House"}
        for obj in objects:
            typ = obj.get("@type")
            if isinstance(typ, list):
                if any(item in preferred_types for item in typ):
                    return obj
            elif isinstance(typ, str) and typ in preferred_types:
                return obj

        for obj in objects:
            if "offers" in obj or "address" in obj:
                return obj
        return None

    def _payload_from_json_ld_listing(self, data: dict[str, Any]) -> dict[str, str]:
        payload: dict[str, str] = {}

        offers = data.get("offers")
        if isinstance(offers, dict):
            price = offers.get("price")
            if price is not None:
                payload["asking_price"] = str(price).strip()

        listing_type = data.get("@type")
        if isinstance(listing_type, list):
            listing_type = next((item for item in listing_type if isinstance(item, str)), None)
        if isinstance(listing_type, str):
            payload["property_type"] = listing_type.strip()

        identifier = data.get("identifier")
        if isinstance(identifier, dict):
            ident_value = identifier.get("value")
            if ident_value is not None:
                payload["source_listing_id"] = str(ident_value).strip()
        elif identifier is not None:
            payload["source_listing_id"] = str(identifier).strip()

        address = data.get("address")
        if isinstance(address, dict):
            city = address.get("addressLocality")
            suburb = address.get("addressRegion") or address.get("addressLocality")
            if city is not None:
                payload["city"] = str(city).strip()
            if suburb is not None:
                payload["suburb"] = str(suburb).strip()

        key_map = {
            "numberOfBedrooms": "bedrooms",
            "numberOfBathroomsTotal": "bathrooms",
            "numberOfParkingSpaces": "parking_spaces",
            "floorSize": "floor_area_sqm",
            "lotSize": "land_area_sqm",
            "datePosted": "listed_at",
        }
        for source_key, target_key in key_map.items():
            value = data.get(source_key)
            if value is not None:
                payload[target_key] = str(value).strip()

        return payload

    @staticmethod
    def _extract_city_suburb_from_title(title: str) -> tuple[str | None, str | None]:
        # Typical title format resembles:
        # "2 Bedroom Apartment for sale in Sandton - P24-123456789"
        if " for " not in title:
            return None, None
        location_part = title.split(" for ", 1)[1]
        if " in " in location_part:
            location_part = location_part.split(" in ", 1)[1]
        location_part = location_part.split("|", 1)[0].split("-", 1)[0].strip()
        if not location_part:
            return None, None
        # Until geocoding exists, map both city/suburb conservatively to parsed location.
        return location_part, location_part

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
