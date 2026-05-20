from scraper.property24 import Property24Adapter
from scraper.sample_data import sample_raw_listing


def test_property24_adapter_normalizes_sample_listing() -> None:
    adapter = Property24Adapter()
    raw = sample_raw_listing()
    normalized = adapter.normalize_listing(raw)

    assert normalized.source == "property24"
    assert normalized.city == "Johannesburg"
    assert normalized.suburb == "Sandton"
    assert normalized.property_type == "Apartment"
    assert normalized.asking_price == 1650000.0
