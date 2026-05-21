from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter
from scraper.property24_scrapegraph import Property24ScrapeGraphAdapter

DEFAULT_SEARCH_URL = "https://www.property24.com/for-sale/gauteng/1"


def _build_adapter(backend: str):
    normalized = backend.strip().lower()
    if normalized == "scrapegraph":
        return Property24ScrapeGraphAdapter()
    if normalized == "html":
        return Property24Adapter()
    raise ValueError(f"Unsupported backend '{backend}'. Use 'html' or 'scrapegraph'.")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run the under-over Property24 scraper.")
    parser.add_argument(
        "--search-url",
        default=os.getenv("UNDER_OVER_SEARCH_URL", DEFAULT_SEARCH_URL),
        help="Property24 search URL. Defaults to .env value or built-in Gauteng URL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.getenv("UNDER_OVER_SCRAPER_LIMIT", "5")),
        help="Maximum listing URLs to discover.",
    )
    parser.add_argument(
        "--backend",
        default=os.getenv("UNDER_OVER_SCRAPER_BACKEND", "scrapegraph"),
        choices=["html", "scrapegraph"],
        help="Scraper backend to use.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=_env_bool("UNDER_OVER_SCRAPER_WRITE", False),
        help="Write normalized records to DB.",
    )
    parser.add_argument(
        "--sample-mode",
        action="store_true",
        help="Run with sample listing payload (no live scraping).",
    )
    args = parser.parse_args()

    adapter = _build_adapter(args.backend)
    result = run_ingestion(
        adapter,
        search_url=args.search_url or None,
        limit=args.limit,
        write_to_db=args.write,
        sample_mode=args.sample_mode,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
