from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.ingestion import run_ingestion
from scraper.property24_camoufox import Property24CamoufoxAdapter

LOCATION_SEARCH_URLS = {
    "gauteng": "https://www.property24.com/for-sale/gauteng/1",
    "cape-town": "https://www.property24.com/for-sale/cape-town/western-cape/432",
    "johannesburg": "https://www.property24.com/for-sale/johannesburg/gauteng/100",
    "durban": "https://www.property24.com/for-sale/durban/kwazulu-natal/146",
    "pretoria": "https://www.property24.com/for-sale/pretoria/gauteng/110",
}
DEFAULT_LOCATION = "gauteng"
DEFAULT_LIMIT = 5


def _log_event(event: str, payload: dict[str, Any]) -> None:
    print(f"[scraper:{event}] {json.dumps(payload, ensure_ascii=False)}")


def _mask_username(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:4]}***"


def _resolve_search_url(location: str, explicit_search_url: str | None) -> str:
    if explicit_search_url and explicit_search_url.strip():
        return explicit_search_url.strip()
    return LOCATION_SEARCH_URLS[location]


def main(
    *,
    location: str = DEFAULT_LOCATION,
    limit: int = DEFAULT_LIMIT,
    search_url_override: str | None = None,
) -> None:
    load_dotenv()
    if location not in LOCATION_SEARCH_URLS:
        valid = ", ".join(sorted(LOCATION_SEARCH_URLS.keys()))
        raise ValueError(f"Unsupported location '{location}'. Valid options: {valid}")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    search_url = _resolve_search_url(location, search_url_override)

    _log_event(
        "startup",
        {
            "backend": "camoufox",
            "location": location,
            "search_url": search_url,
            "limit": limit,
            "write_to_db": False,
            "sample_mode": False,
        },
    )
    _log_event(
        "stealth_connection",
        {
            "stealth_package": "stealth-scraping",
            "proxy_enabled": os.getenv("STEALTH_PROXY_ENABLED", "true"),
            "proxy_server": os.getenv("STEALTH_PROXY_SERVER", "http://t.pr.thordata.net:9999"),
            "proxy_username": _mask_username(os.getenv("STEALTH_PROXY_USERNAME", "")),
        },
    )
    adapter = Property24CamoufoxAdapter()
    _log_event(
        "adapter_selected",
        {"adapter_source": adapter.source_name, "requested_backend": "camoufox"},
    )
    result = run_ingestion(
        adapter,
        search_url=search_url,
        limit=limit,
        sample_mode=False,
        progress_callback=_log_event,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
