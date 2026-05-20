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
