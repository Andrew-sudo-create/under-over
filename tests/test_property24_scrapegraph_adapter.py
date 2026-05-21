from urllib.parse import parse_qs, urlparse

from scraper.property24_scrapegraph import Property24ScrapeGraphAdapter


def test_discover_listing_urls_paginates_until_limit(monkeypatch) -> None:
    adapter = Property24ScrapeGraphAdapter()

    def fake_run_scrapegraph(self, *, website_url: str, user_prompt: str):  # noqa: ARG001
        page = int(parse_qs(urlparse(website_url).query).get("Page", ["1"])[0])
        if page == 1:
            return {
                "listing_urls": [
                    "https://www.property24.com/for-sale/a/b/c/1/111111111",
                    "https://www.property24.com/for-sale/a/b/c/1/222222222",
                ]
            }
        if page == 2:
            return {
                "listing_urls": [
                    "https://www.property24.com/for-sale/a/b/c/1/333333333",
                    "https://www.property24.com/for-sale/a/b/c/1/444444444",
                ]
            }
        return {"listing_urls": []}

    monkeypatch.setattr(Property24ScrapeGraphAdapter, "_run_scrapegraph", fake_run_scrapegraph)

    urls = adapter.discover_listing_urls("https://www.property24.com/for-sale/gauteng/1", limit=3)
    assert urls == [
        "https://www.property24.com/for-sale/a/b/c/1/111111111",
        "https://www.property24.com/for-sale/a/b/c/1/222222222",
        "https://www.property24.com/for-sale/a/b/c/1/333333333",
    ]


def test_discover_listing_urls_stops_when_no_new_urls(monkeypatch) -> None:
    adapter = Property24ScrapeGraphAdapter()

    def fake_run_scrapegraph(self, *, website_url: str, user_prompt: str):  # noqa: ARG001
        page = int(parse_qs(urlparse(website_url).query).get("Page", ["1"])[0])
        if page == 1:
            return {"listing_urls": ["https://www.property24.com/for-sale/a/b/c/1/111111111"]}
        # page 2 repeats the same URL, which should trigger stop condition
        return {"listing_urls": ["https://www.property24.com/for-sale/a/b/c/1/111111111"]}

    monkeypatch.setattr(Property24ScrapeGraphAdapter, "_run_scrapegraph", fake_run_scrapegraph)

    urls = adapter.discover_listing_urls("https://www.property24.com/for-sale/gauteng/1", limit=5)
    assert urls == ["https://www.property24.com/for-sale/a/b/c/1/111111111"]
