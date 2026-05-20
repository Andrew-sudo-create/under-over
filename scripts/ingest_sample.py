from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert sample listing data into under-over database.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write to database. Without this flag, command runs in dry-run mode.",
    )
    args = parser.parse_args()

    result = run_ingestion(
        Property24Adapter(),
        write_to_db=args.write,
        sample_mode=True,
    )
    print(result.to_dict())


if __name__ == "__main__":
    main()
