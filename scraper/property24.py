from __future__ import annotations

from datetime import datetime
import json
import re
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
                    if not self._is_listing_detail_url(absolute):
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
        if not self._is_listing_detail_url(listing_url):
            raise ValueError(
                "listing_url must be a listing detail page URL (not a search/suburb page). "
                "Use /scraper/discover first and pass one of the discovered detail URLs."
            )
        with self.guard.build_client() as client:
            response = self.guard.get(client, listing_url)

        payload = self._extract_payload_from_html(response.text)
        city_from_url, suburb_from_url = self.extract_city_suburb_from_listing_url(listing_url)
        selected_city = self._choose_city(payload.get("city"), city_from_url)
        if selected_city:
            payload["city"] = selected_city
        if suburb_from_url and "suburb" not in payload:
            payload["suburb"] = suburb_from_url

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
            if parsed.netloc.endswith("property24.com") and self._is_listing_detail_url(absolute):
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
                graph = data.get("@graph")
                if isinstance(graph, list):
                    objects.extend([item for item in graph if isinstance(item, dict)])
                else:
                    objects.append(data)
            elif isinstance(data, list):
                objects.extend([item for item in data if isinstance(item, dict)])
        return objects

    @staticmethod
    def _pick_listing_object(objects: list[dict[str, Any]]) -> dict[str, Any] | None:
        preferred_types = {
            "RealEstateListing",
            "Offer",
            "Product",
            "Residence",
            "SingleFamilyResidence",
            "Apartment",
            "House",
        }
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
            if price is None:
                price_spec = offers.get("priceSpecification")
                if isinstance(price_spec, dict):
                    price = price_spec.get("price")
            if price is not None:
                payload["asking_price"] = str(price).strip()

        listing_type = data.get("@type")
        if isinstance(listing_type, list):
            listing_type = next((item for item in listing_type if isinstance(item, str)), None)
        if isinstance(listing_type, str) and listing_type != "RealEstateListing":
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

        about = data.get("about")
        if isinstance(about, dict):
            about_type = about.get("@type")
            if isinstance(about_type, str):
                payload["property_type"] = about_type.strip()
            about_address = about.get("address")
            if isinstance(about_address, dict):
                locality = about_address.get("addressLocality")
                region = about_address.get("addressRegion")
                if locality is not None:
                    payload["suburb"] = str(locality).strip()
                if region is not None and "city" not in payload:
                    payload["city"] = str(region).strip()

            for source_key, target_key in {
                "numberOfBedrooms": "bedrooms",
                "numberOfBathroomsTotal": "bathrooms",
                "numberOfParkingSpaces": "parking_spaces",
                "floorSize": "floor_area_sqm",
                "lotSize": "land_area_sqm",
            }.items():
                value = about.get(source_key)
                if value is not None:
                    payload[target_key] = str(value).strip()

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
    def extract_city_suburb_from_listing_url(url: str) -> tuple[str | None, str | None]:
        parsed = urlparse(url)
        segments = [segment for segment in parsed.path.split("/") if segment]
        # Expected pattern:
        # /for-sale/<suburb>/<city>/<province>/<area-id>/<listing-id>
        if len(segments) < 6:
            return None, None
        if segments[0] not in {"for-sale", "to-rent"}:
            return None, None
        suburb_slug = segments[1]
        city_slug = segments[2]
        return Property24Adapter._slug_to_text(city_slug), Property24Adapter._slug_to_text(suburb_slug)

    @staticmethod
    def _slug_to_text(value: str) -> str:
        cleaned = re.sub(r"[-_]+", " ", value).strip()
        return " ".join(word.capitalize() for word in cleaned.split())

    @staticmethod
    def _choose_city(extracted_city: str | None, city_from_url: str | None) -> str | None:
        if city_from_url is None:
            return extracted_city
        if extracted_city is None:
            return city_from_url

        provinces = {
            "Gauteng",
            "Western Cape",
            "KwaZulu Natal",
            "KwaZulu-Natal",
            "Free State",
            "Mpumalanga",
            "Eastern Cape",
            "North West",
            "Limpopo",
            "Northern Cape",
        }
        if extracted_city in provinces:
            return city_from_url
        return extracted_city

    @staticmethod
    def _parse_iso_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _is_listing_detail_url(url: str) -> bool:
        parsed = urlparse(url)
        if not parsed.netloc.endswith("property24.com"):
            return False
        segments = [segment for segment in parsed.path.split("/") if segment]
        if len(segments) < 2:
            return False
        # Detail pages usually end in a long numeric listing id.
        last = segments[-1]
        return last.isdigit() and len(last) >= 6
