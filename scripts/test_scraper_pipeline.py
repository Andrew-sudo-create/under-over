from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print(f"-> {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False)
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test under-over scraper pipeline.")
    parser.add_argument("--search-url", help="Optional live search URL for dry-run ingestion test.")
    parser.add_argument("--limit", type=int, default=2, help="Limit for live discovery dry-run.")
    args = parser.parse_args()

    steps: list[tuple[str, list[str]]] = [
        ("Unit tests", [sys.executable, "-m", "pytest", "-q"]),
        ("Sample dry-run ingestion", [sys.executable, "scripts/ingest_sample.py"]),
    ]

    if args.search_url:
        steps.append(
            (
                "Live dry-run ingestion",
                [
                    sys.executable,
                    "scripts/run_ingestion.py",
                    "--search-url",
                    args.search_url,
                    "--limit",
                    str(args.limit),
                ],
            )
        )

    for name, command in steps:
        print(f"\n=== {name} ===")
        code = _run(command)
        if code != 0:
            raise SystemExit(code)

    print("\nScraper pipeline smoke test passed.")


if __name__ == "__main__":
    main()
