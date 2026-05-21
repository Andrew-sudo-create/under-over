from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api import main
from scraper.base import NormalizedListing, RawListing


client = TestClient(main.app)


class FakeAdapter:
    source_name = "property24"

    def discover_listing_urls(self, search_url: str, limit: int = 20) -> list[str]:
        return [f"{search_url.rstrip('/')}/listing-{i}" for i in range(1, limit + 1)]

    def fetch_listing(self, listing_url: str) -> RawListing:
        return RawListing(
            source=self.source_name,
            listing_url=listing_url,
            source_listing_id="abc123",
            payload={"asking_price": "1650000", "city": "Johannesburg", "suburb": "Sandton"},
            scraped_at=datetime.now(timezone.utc),
        )

    def normalize_listing(self, raw: RawListing) -> NormalizedListing:
        return NormalizedListing(
            listing_url=raw.listing_url,
            source=raw.source,
            city="Johannesburg",
            suburb="Sandton",
            property_type="Apartment",
            asking_price=1650000.0,
            first_seen_at=raw.scraped_at,
            last_seen_at=raw.scraped_at,
        )


class FakeStrictAdapter(FakeAdapter):
    def fetch_listing(self, listing_url: str) -> RawListing:
        if listing_url.endswith("/for-sale/gauteng/1"):
            raise ValueError("listing_url must be a listing detail page URL")
        return super().fetch_listing(listing_url)


def test_scraper_discover_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(main, "Property24Adapter", FakeAdapter)

    response = client.post(
        "/api/v1/scraper/discover",
        json={"search_url": "https://example.com/search", "limit": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["count"] == 2


def test_scraper_fetch_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(main, "Property24Adapter", FakeAdapter)

    response = client.post(
        "/api/v1/scraper/fetch",
        json={"listing_url": "https://example.com/listing-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["raw"]["source_listing_id"] == "abc123"


def test_scraper_normalize_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(main, "Property24Adapter", FakeAdapter)

    response = client.post(
        "/api/v1/scraper/normalize",
        json={"listing_url": "https://example.com/listing-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["normalized"]["asking_price"] == 1650000.0
    assert payload["missing_critical_fields"] == []


def test_scraper_normalize_rejects_search_page_url(monkeypatch) -> None:
    monkeypatch.setattr(main, "Property24Adapter", FakeStrictAdapter)

    response = client.post(
        "/api/v1/scraper/normalize",
        json={"listing_url": "https://www.property24.com/for-sale/gauteng/1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert "listing detail page URL" in payload["message"]


def test_scraper_discover_uses_scrapegraph_backend(monkeypatch) -> None:
    monkeypatch.setattr(main, "Property24ScrapeGraphAdapter", FakeAdapter)

    response = client.post(
        "/api/v1/scraper/discover",
        json={"search_url": "https://example.com/search", "limit": 2, "backend": "scrapegraph"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["source"] == "property24"
    assert payload["count"] == 2


def test_scraper_discover_rejects_invalid_backend() -> None:
    response = client.post(
        "/api/v1/scraper/discover",
        json={"search_url": "https://example.com/search", "limit": 2, "backend": "invalid"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert "unsupported backend" in payload["message"]
