from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from scrapegraph_py import FetchConfig, JsonFormatConfig, ScrapeGraphAI

from api.config import settings
from scraper.base import RawListing, utcnow
from scraper.property24 import Property24Adapter


class Property24ScrapeGraphAdapter(Property24Adapter):
    source_name = "property24-scrapegraph"

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        urls: list[str] = []
        seen: set[str] = set()
        page = 1

        while len(urls) < limit:
            paged_url = self._with_page(search_url, page)
            prompt = (
                "Extract property listing URLs from this Property24 search page. "
                "Return JSON with either {'listings':[{'property_url':'...'}]} or "
                "{'listing_urls':['...']}. Include only listing detail page URLs."
            )
            extracted = self._run_scrapegraph(
                website_url=paged_url,
                user_prompt=prompt,
            )

            newly_added = 0
            for raw_url in self._extract_discovered_urls(extracted):
                absolute = urljoin(search_url, raw_url.strip().split("?")[0])
                if not self._is_listing_detail_url(absolute):
                    continue
                if absolute in seen:
                    continue
                seen.add(absolute)
                urls.append(absolute)
                newly_added += 1
                if len(urls) >= limit:
                    break

            if newly_added == 0:
                break
            page += 1

        return urls

    def fetch_listing(self, listing_url: str) -> RawListing:
        if not self._is_listing_detail_url(listing_url):
            raise ValueError(
                "listing_url must be a listing detail page URL (not a search/suburb page). "
                "Use /scraper/discover first and pass one of the discovered detail URLs."
            )

        prompt = (
            "Extract this Property24 listing as JSON with keys: source_listing_id, city, suburb, "
            "property_type, bedrooms, bathrooms, parking_spaces, floor_area_sqm, land_area_sqm, "
            "asking_price, listed_at, title. Use text values when uncertain."
        )
        payload = self._run_scrapegraph(
            website_url=listing_url,
            user_prompt=prompt,
        )
        if isinstance(payload.get("listing"), dict):
            payload = payload["listing"]

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

    def _run_scrapegraph(
        self,
        *,
        website_url: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if not settings.scrapegraph_api_key:
            raise ValueError(
                "ScrapeGraph backend selected but UNDER_OVER_SCRAPEGRAPH_API_KEY is not configured."
            )

        sgai = ScrapeGraphAI(api_key=settings.scrapegraph_api_key)
        timeout_ms = min(int(settings.scrapegraph_timeout_seconds * 1000), 60000)
        response = sgai.scrape(
            website_url,
            formats=[JsonFormatConfig(prompt=user_prompt, mode="normal")],
            fetch_config=FetchConfig(
                mode="auto",
                stealth=False,
                timeout=timeout_ms,
                wait=0,
                scrolls=0,
                mock=False,
            ),
        )
        if response.status != "success":
            raise ValueError(f"scrapegraph_failed: {response.error}")

        data = response.data.model_dump() if hasattr(response.data, "model_dump") else response.data
        if not isinstance(data, dict):
            raise ValueError("Unexpected ScrapeGraph response shape.")

        results = data.get("results")
        if isinstance(results, dict):
            json_result = results.get("json")
            if isinstance(json_result, dict):
                json_data = json_result.get("data")
                if isinstance(json_data, dict):
                    return json_data
        return data

    @staticmethod
    def _extract_discovered_urls(payload: dict[str, Any]) -> list[str]:
        urls: list[str] = []

        listing_urls = payload.get("listing_urls")
        if isinstance(listing_urls, list):
            for item in listing_urls:
                if isinstance(item, str) and item.strip():
                    urls.append(item)

        listings = payload.get("listings")
        if isinstance(listings, list):
            for item in listings:
                if not isinstance(item, dict):
                    continue
                value = item.get("property_url")
                if isinstance(value, str) and value.strip():
                    urls.append(value)

        return urls
