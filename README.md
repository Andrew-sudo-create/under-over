# under-over

Property24 scraping app powered by the external `stealth-scraping` package.

This repository is intentionally focused on one job:
- discover Property24 listing URLs for a chosen location
- scrape each listing page
- normalize key property fields
- print structured logs + final JSON run summary

## Repository description

**Developer-ready Property24 scraper that uses `stealth-scraping` for Camoufox/Playwright stealth execution and proxy support.**

## Project layout

- `run_scarper.py` - entrypoint; set `LOCATION` and `LIMIT` in code
- `scripts/run_scraper.py` - runner + structured logging
- `scraper/property24_camoufox.py` - stealth-backed adapter
- `scraper/property24.py` - Property24 URL discovery and HTML parsing
- `scraper/ingestion.py` - discover/fetch/normalize workflow

## Prerequisites

- Python 3.11+
- Access to `stealth-scraping` package
- Playwright Firefox runtime
- Valid proxy credentials (if proxy enabled)

## Installation

1. Install this repo dependencies:
   - `python -m pip install -r requirements.txt`
2. Install stealth package:
   - `python -m pip install "git+https://github.com/<your-org>/stealth-scraping.git"`
3. Install browser runtime:
   - `python -m playwright install firefox`
4. Configure env:
   - `copy .env.example .env`
   - set `STEALTH_PROXY_USERNAME` and `STEALTH_PROXY_PASSWORD`

## Configuration

### Code-level config

Edit `run_scarper.py`:
- `LOCATION = "gauteng"`
- `LIMIT = 30`

Supported location keys:
- `gauteng`
- `cape-town`
- `johannesburg`
- `durban`
- `pretoria`

### Environment config

Defined in `.env`:
- `STEALTH_HEADLESS`
- `STEALTH_PROXY_ENABLED`
- `STEALTH_PROXY_SERVER`
- `STEALTH_PROXY_USERNAME`
- `STEALTH_PROXY_PASSWORD`

## Run

- `python run_scarper.py`

Output includes:
- run lifecycle logs (startup, discovery, finish)
- per-listing extracted fields
- final JSON summary

## Troubleshooting

- `ModuleNotFoundError: stealth_scraping`
  - reinstall stealth package from git
- Browser launch errors
  - run `python -m playwright install firefox`
- Proxy auth failures
  - verify `STEALTH_PROXY_USERNAME` and `STEALTH_PROXY_PASSWORD`

## Extension notes

- Keep stealth concerns in `stealth-scraping`.
- Keep Property24-specific parsing in this repo.
- To add locations, update `LOCATION_SEARCH_URLS` in `scripts/run_scraper.py`.

