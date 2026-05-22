from __future__ import annotations

from scraper.base import RawListing, utcnow
from scraper.property24 import Property24Adapter

from stealth_scraping import open_stealth_page


class Property24CamoufoxAdapter(Property24Adapter):
    source_name = "property24_camoufox"

    def __init__(
        self,
        *,
        headless: bool | None = None,
        navigation_timeout_ms: int | None = None,
    ) -> None:
        super().__init__()
        self.headless = headless
        self.navigation_timeout_ms = navigation_timeout_ms

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        if not self.guard.can_fetch(search_url):
            raise PermissionError(f"robots.txt disallows scraping: {search_url}")

        found: list[str] = []
        seen: set[str] = set()
        page = 1

        with open_stealth_page() as page_obj:
            while len(found) < limit:
                paged_url = self._with_page(search_url, page)
                self.guard.wait_with_jitter()
                page_obj.goto(paged_url, wait_until="domcontentloaded")
                html = page_obj.content()
                urls = self._extract_listing_urls(html, search_url)
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
        if not self.guard.can_fetch(listing_url):
            raise PermissionError(f"robots.txt disallows scraping: {listing_url}")

        with open_stealth_page() as page_obj:
            self.guard.wait_with_jitter()
            page_obj.goto(listing_url, wait_until="domcontentloaded")
            html = page_obj.content()

        payload = self._extract_payload_from_html(html)
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
