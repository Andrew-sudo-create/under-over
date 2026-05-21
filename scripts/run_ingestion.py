from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter
from scraper.property24_scrapegraph import Property24ScrapeGraphAdapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Run under-over listing ingestion.")
    parser.add_argument("--search-url", required=True, help="Property search URL to discover listing pages.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum listing URLs to discover.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write normalized outputs to DB. Without this flag, run in dry-run mode.",
    )
    parser.add_argument(
        "--backend",
        default="html",
        choices=["html", "scrapegraph"],
        help="Scraper backend to use.",
    )
    args = parser.parse_args()

    if args.backend == "scrapegraph":
        adapter = Property24ScrapeGraphAdapter()
    else:
        adapter = Property24Adapter()

    result = run_ingestion(
        adapter,
        search_url=args.search_url,
        limit=args.limit,
        write_to_db=args.write,
        sample_mode=False,
    )
    print(result.to_dict())


if __name__ == "__main__":
    main()
