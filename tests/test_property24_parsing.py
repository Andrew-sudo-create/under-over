from pathlib import Path

from scraper.property24 import Property24Adapter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_extract_listing_urls_from_search_html() -> None:
    html = (FIXTURES_DIR / "property24_search_sample.html").read_text(encoding="utf-8")
    adapter = Property24Adapter()

    urls = adapter._extract_listing_urls(html, "https://www.property24.com/for-sale/sandton/gauteng/109")

    assert len(urls) == 3
    assert urls[0] == "https://www.property24.com/for-sale/sandton/johannesburg/gauteng/109/123456789"
    assert urls[1] == "https://www.property24.com/for-sale/sandton/johannesburg/gauteng/109/987654321"


def test_listing_detail_url_validator() -> None:
    adapter = Property24Adapter()

    assert adapter._is_listing_detail_url("https://www.property24.com/for-sale/sandton/johannesburg/gauteng/109/123456789")
    assert not adapter._is_listing_detail_url("https://www.property24.com/for-sale/gauteng/1")


def test_extract_payload_from_listing_html() -> None:
    html = (FIXTURES_DIR / "property24_listing_sample.html").read_text(encoding="utf-8")
    adapter = Property24Adapter()

    payload = adapter._extract_payload_from_html(html)

    assert payload["source_listing_id"] == "123456789"
    assert payload["asking_price"] == "1650000"
    assert payload["city"] == "Johannesburg"
    assert payload["suburb"] == "Sandton"
    assert payload["bedrooms"] == "2"
    assert payload["floor_area_sqm"] == "89"


def test_extract_payload_from_graph_listing_html() -> None:
    html = (FIXTURES_DIR / "property24_listing_graph_sample.html").read_text(encoding="utf-8")
    adapter = Property24Adapter()

    payload = adapter._extract_payload_from_html(html)

    assert payload["asking_price"] == "540000"
    assert payload["property_type"] == "House"
    assert payload["bedrooms"] == "3"
    assert payload["bathrooms"] == "1"
    assert payload["suburb"] == "Tsakane Ext 8"
    assert payload["listed_at"] == "2025-05-16"


def test_extract_city_suburb_from_listing_url() -> None:
    adapter = Property24Adapter()
    city, suburb = adapter.extract_city_suburb_from_listing_url(
        "https://www.property24.com/for-sale/tsakane-ext-8/brakpan/gauteng/1074/115979763"
    )
    assert city == "Brakpan"
    assert suburb == "Tsakane Ext 8"


def test_choose_city_prefers_url_over_province_value() -> None:
    adapter = Property24Adapter()
    assert adapter._choose_city("Gauteng", "Brakpan") == "Brakpan"
    assert adapter._choose_city("Johannesburg", "Brakpan") == "Johannesburg"
