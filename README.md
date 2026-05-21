# under-over

`under-over` is a property valuation tool focused on helping everyday home buyers identify potential bargains.

## Core Idea

The app pipeline is:

1. Scrape property listing data from local real estate websites.
2. Store normalized records in a structured database.
3. Aggregate neighborhood and historical market signals.
4. Run valuation models to classify listings as:
   - Undervalued
   - Fairly priced
   - Overvalued

## Case Study

Project progress is documented as an ongoing build log in:

- `docs/case-study.md`
- `docs/github-projects-30-day-board.md`
- `docs/mvp-scope.md`

Each entry captures objectives, technical decisions, results, blockers, and next steps.

## Quickstart

1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Run tests:
   - `python -m pytest -q`
3. Run API:
   - `python -m uvicorn api.main:app --reload`

Health endpoint:

- `GET /health`

## Day 2 ingestion scaffold

- Dry run sample ingestion:
  - `python scripts/ingest_sample.py`
- Write sample ingestion to Postgres:
  - `python scripts/ingest_sample.py --write`

Notes:

- The Property24 adapter is currently a compliance-first starter.
- `robots.txt` checks are enforced before discovery/fetch operations.

## Day 3 orchestration and DB bootstrap

- Apply schema to database:
  - `python scripts/bootstrap_db.py`
- Run live ingestion (dry-run):
  - `python scripts/run_ingestion.py --search-url "<property-search-url>" --limit 3`
- Run sample ingestion via API:
  - `POST /api/v1/ingestion/run` with `{"sample_mode": true}`
- Check last ingestion status:
  - `GET /api/v1/ingestion/status`
- Check latest ingestion quality summary:
  - `GET /api/v1/ingestion/summary`
- Check recent ingestion run trends (from DB):
  - `GET /api/v1/ingestion/trends?limit=10`
- Check DB-backed data quality report:
  - `GET /api/v1/data-quality/report`

## Scraper pipeline test

Run the full scraper smoke test:

- `python scripts/test_scraper_pipeline.py`

Run with a live search URL (dry-run fetch and parse):

- `python scripts/test_scraper_pipeline.py --search-url "https://www.property24.com/for-sale/gauteng/1"`

## ScrapeGraph backend (Property24)

You can switch the scraper backend from HTML parsing (`html`, default) to ScrapeGraph (`scrapegraph`).

Configure env vars:

- `UNDER_OVER_SCRAPEGRAPH_API_KEY=<your-key>`
- `UNDER_OVER_SCRAPEGRAPH_ENDPOINT=https://api.scrapegraphai.com/v1/smartscraper`
- `UNDER_OVER_SCRAPEGRAPH_TIMEOUT_SECONDS=120`

Run ingestion with ScrapeGraph:

- `python scripts/run_ingestion.py --search-url "https://www.property24.com/for-sale/gauteng/1" --limit 3 --backend scrapegraph`

## Postman testing (real scraper functions)

Start API:

- `python -m uvicorn api.main:app --reload`

Base URL:

- `http://127.0.0.1:8000`

Use these endpoints in Postman:

- `POST /api/v1/scraper/discover`
  - body:
    - `{"search_url":"https://www.property24.com/for-sale/gauteng/1","limit":5,"backend":"html"}`
    - `{"search_url":"https://www.property24.com/for-sale/gauteng/1","limit":5,"backend":"scrapegraph"}`
- `POST /api/v1/scraper/fetch`
  - body:
    - `{"listing_url":"https://www.property24.com/for-sale/...","backend":"html"}`
    - `{"listing_url":"https://www.property24.com/for-sale/...","backend":"scrapegraph"}`
- `POST /api/v1/scraper/normalize`
  - body:
    - `{"listing_url":"https://www.property24.com/for-sale/...","backend":"html"}`
    - `{"listing_url":"https://www.property24.com/for-sale/...","backend":"scrapegraph"}`
- `POST /api/v1/ingestion/run`
  - sample dry-run:
    - `{"sample_mode":true,"write_to_db":false}`
  - live dry-run:
    - `{"search_url":"https://www.property24.com/for-sale/gauteng/1","limit":3,"write_to_db":false}`
- `GET /api/v1/ingestion/status`
- `GET /api/v1/ingestion/summary`
- `GET /api/v1/ingestion/trends?limit=10` (requires DB + schema applied)
- `GET /api/v1/data-quality/report` (requires DB + schema applied)

Prebuilt Postman collection:

- `postman/under-over.postman_collection.json`
