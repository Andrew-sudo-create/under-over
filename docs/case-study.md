# under-over Case Study

This document tracks the development journey of `under-over` from concept to production-ready valuation platform.

---

## Day 0 - Project Framing

### Objective
Define the product concept, core architecture, and execution roadmap for a property valuation app.

### Actions Taken
- Clarified target audience: everyday home buyers and bargain hunters.
- Defined core flow: scrape listings -> store in structured DB -> run valuation model -> classify as under/fair/over priced.
- Chose model strategy: ML as core valuation engine, LLM as explanation layer.
- Drafted a 30-day roadmap and phased delivery plan.

### Technical Decisions
- Decision: Use ML (CatBoost/LightGBM) for valuation.
- Reason: Better pricing accuracy and reliability than LLM for numeric estimation.
- Tradeoff: Requires stronger data engineering and feature quality.

### Results
- Clear MVP scope and architecture direction established.
- Free-first deployment path identified (GitHub + free DB/hosting tiers).

### Challenges
- Concern about anti-scraping/IP blocking from property portals.
- Need a compliant and sustainable data collection strategy.

### What I Learned
- Valuation accuracy mostly comes from data quality and feature engineering, not LLM choice.
- LLM is best used for explainability, not core price prediction.

### Next Milestone
- Define v1 schema, API contracts, and first scraper design for one source and one region.

---

## Day 1 - Project Scaffold and Execution Setup

### Objective
Initialize the `under-over` codebase with a runnable backend skeleton, starter data schema, and clear MVP scope defaults.

### Actions Taken
- Created project folders: `api`, `scraper`, `model`, `db`, and `tests`.
- Added FastAPI starter app with `/` and `/health` endpoints.
- Added environment-based configuration via `pydantic-settings`.
- Added initial SQL schema for raw listings, normalized listings, and price history.
- Added baseline API test and installed project dependencies.
- Added MVP scope document and quickstart instructions.

### Technical Decisions
- Decision: Start with FastAPI and a small health-first API skeleton.
- Reason: Fast iteration speed and clear path to valuation endpoints and MCP wrapping.
- Tradeoff: Initial implementation is minimal and does not include ingestion logic yet.

### Results
- Output: Runnable Python backend scaffold with initial DB design and tests.
- Metrics: `1 passed` test in local run (`python -m pytest -q`).
- Quality check: Health endpoint contract validated in automated test.

### Challenges
- `pytest` was not available in the local environment initially.
- Python user-level scripts path is not on `PATH` (warning only, non-blocking).

### What I Learned
- Establishing a tested scaffold on Day 1 reduces setup drag in later phases.
- Early schema structure for history tracking is important for valuation features.

### Next Milestone
- Build Day 2: first ingestion adapter interface and compliance-first scraper rules.

---

## Day 2 - Compliance-first Scraper and Ingestion Skeleton

### Objective
Create the first ingestion adapter interface, establish compliance-first scraping rules, and add a sample ingestion flow into database tables.

### Actions Taken
- Added scraper contracts and data models in `scraper/base.py`.
- Added normalization utilities for numeric and text fields in `scraper/normalize.py`.
- Added compliance guard with `robots.txt` checks and jittered delays in `scraper/compliance.py`.
- Added Property24 adapter scaffold in `scraper/property24.py` (discovery, fetch, normalize).
- Added sample data fixture and ingestion command (`scripts/ingest_sample.py`) with dry-run/write modes.
- Added tests for normalization and adapter normalization output.
- Added compliance notes in `docs/scraping-compliance.md`.

### Technical Decisions
- Decision: enforce robots checks and fail closed when robots cannot be validated.
- Reason: compliance-first posture is safer and more sustainable for an early-stage product.
- Tradeoff: stricter rules may reduce data coverage in environments with blocked robots access.

### Results
- Output: runnable ingestion skeleton from sample raw payload to normalized insert logic.
- Metrics: 5 automated tests passing locally.
- Quality check: test coverage now includes API health, normalization, and adapter mapping behavior.

### Challenges
- Needed DB-write flow without assuming local Postgres availability.
- Kept ingestion command safe by default via dry-run mode.

### What I Learned
- Defining adapter contracts early keeps source-specific scraping isolated and replaceable.
- Normalization utilities prevent parsing logic from leaking across ingestion code.

### Next Milestone
- Build Day 3: database bootstrap command, first real discovery endpoint wiring, and ingestion orchestration entrypoint.

---

## Day 3 - DB Bootstrap and Ingestion Orchestration

### Objective
Move from isolated ingestion helpers to a reusable ingestion workflow that can run from scripts and API endpoints.

### Actions Taken
- Created reusable DB persistence module in `db/persistence.py`.
- Added ingestion orchestrator in `scraper/ingestion.py` with result tracking and error collection.
- Refactored sample ingestion script to use orchestrator.
- Added `scripts/bootstrap_db.py` to apply `db/schema.sql` directly to Postgres.
- Added `scripts/run_ingestion.py` for live discovery/fetch/normalize workflows.
- Added API ingestion endpoints:
  - `POST /api/v1/ingestion/run`
  - `GET /api/v1/ingestion/status`
- Added tests for ingestion workflow and ingestion API behavior.

### Technical Decisions
- Decision: centralize ingestion logic into `run_ingestion(...)` and reuse it from both API and scripts.
- Reason: reduces drift between manual scripts and service endpoints.
- Tradeoff: API endpoint currently runs synchronously; async background jobs can be added later.

### Results
- Output: end-to-end ingestion orchestration with dry-run and optional DB writes.
- Metrics: 8 automated tests passing locally.
- Quality check: sample-mode ingestion validated via both unit and API tests.

### Challenges
- Needed to keep DB writes optional to support no-DB local development.
- Avoided duplicate SQL logic by extracting persistence functions.

### What I Learned
- Reusable orchestration early makes scheduler/cron integration easier later.
- Returning a structured ingestion result object simplifies observability and debugging.

### Next Milestone
- Build Day 4: first data quality checks and ingestion summary endpoint with basic metrics (missing fields, duplicates, parse failures).

---

## Day 4 - Ingestion Quality Metrics and Summary Endpoint

### Objective
Add quality checks to ingestion outputs so each run reports data completeness and failure metrics, not just record counts.

### Actions Taken
- Extended `IngestionResult` with a `quality_summary` payload.
- Added quality metrics in ingestion orchestration:
  - duplicate discovered URLs
  - missing critical fields (city, suburb, property type, asking price)
  - parse/listing failure counts
- Added API endpoint `GET /api/v1/ingestion/summary` for quick monitoring.
- Updated tests to assert quality metrics and summary endpoint behavior.
- Updated README to include summary endpoint usage.

### Technical Decisions
- Decision: compute quality metrics in the ingestion layer, then expose via API.
- Reason: keeps monitoring consistent across script and API-triggered runs.
- Tradeoff: metrics are currently scoped to latest run in memory, not persisted historically yet.

### Results
- Output: ingestion runs now include structured quality telemetry.
- Metrics: 9 automated tests passing locally.
- Quality check: summary endpoint returns expected processed and missing-critical counts.

### Challenges
- Needed metrics that are useful immediately without introducing extra DB tables.
- Balanced minimal implementation with future extensibility.

### What I Learned
- Basic quality telemetry quickly surfaces ingestion regressions before model training.
- A dedicated summary endpoint makes operational checks straightforward.

### Next Milestone
- Build Day 5: persist ingestion run history and expose trend view across runs.

---

## Day 5 - Persisted Ingestion Run History and Trends API

### Objective
Persist ingestion run metadata to Postgres and expose a trend view so data-quality progress can be tracked over multiple runs.

### Actions Taken
- Extended schema with `ingestion_runs` table and `created_at` index.
- Added `db/ingestion_runs.py` with:
  - `save_ingestion_run(...)`
  - `get_recent_ingestion_runs(...)`
- Updated ingestion orchestrator to save each run result when DB-write mode is enabled.
- Added new API endpoint:
  - `GET /api/v1/ingestion/trends?limit=10`
- Updated API tests to validate trends endpoint behavior using monkeypatching.
- Updated README with trends endpoint usage.

### Technical Decisions
- Decision: persist run history only when `write_to_db=True`.
- Reason: avoids forcing DB connectivity for dry-run/local exploration workflows.
- Tradeoff: dry runs are still visible in memory status but not in persistent trend history.

### Results
- Output: ingestion quality telemetry now has a persistent historical record in DB mode.
- Metrics: 10 automated tests passing locally.
- Quality check: trends endpoint returns persisted runs and count metadata.

### Challenges
- Avoided import-cycle risk between ingestion orchestration and run-history persistence.
- Ensured DB connection cleanup remains safe in all ingestion flow paths.

### What I Learned
- Persisting run-level telemetry early makes operational maturity and debugging easier later.
- A trends endpoint is a simple but high-value observability primitive for ingestion pipelines.

### Next Milestone
- Build Day 6: add first data-quality report endpoint from DB tables (coverage by city/suburb, null-rate dashboard).

---

## Day 6 - DB-backed Data Quality Report

### Objective
Expose DB-level data quality metrics to evaluate listing completeness and city coverage after ingestion runs.

### Actions Taken
- Added `db/quality.py` to compute:
  - total normalized rows
  - missing rates for city/suburb/property_type/asking_price
  - top city coverage with missing-price counts
- Added API endpoint:
  - `GET /api/v1/data-quality/report`
- Added API test for report endpoint using mocked quality data.
- Updated README with quality report endpoint reference.

### Technical Decisions
- Decision: compute quality in SQL against `listings_normalized` rather than in-memory run payloads.
- Reason: reflects actual persisted state used by downstream modeling.
- Tradeoff: endpoint depends on DB availability and schema bootstrap completion.

### Results
- Output: operator-friendly quality report endpoint for post-ingestion verification.
- Metrics: expanded automated API test coverage.
- Quality check: endpoint response shape validated in tests.

### Challenges
- Needed to avoid coupling quality report logic to ingestion-memory state.
- Ensured graceful API error response when DB is unavailable.

### What I Learned
- Persistent table-level metrics are more reliable for training readiness checks.
- Small quality dashboards create a clear “go/no-go” gate before model training.

### Next Milestone
- Harden scraper parsing and retry behavior for better real-world resilience.

---

## Day 7 - Scraper Hardening (Retries, Pagination, Richer Parsing)

### Objective
Increase scraper robustness and extraction fidelity so live dry-run tests are meaningful and stable.

### Actions Taken
- Enhanced compliance guard:
  - retry with exponential backoff on `429/5xx`
  - centralized guarded `get(...)` method
- Upgraded Property24 adapter:
  - paginated URL discovery (`Page` query parameter)
  - reusable HTML listing-url extraction
  - richer JSON-LD extraction (price, identifiers, bedrooms, bathrooms, sizes, date, address)
  - fallback location parsing from title when city/suburb missing
- Added fixture-based parser tests for:
  - search page URL extraction
  - listing page payload extraction

### Technical Decisions
- Decision: test parser logic with HTML fixtures to reduce live-network test fragility.
- Reason: deterministic tests speed up iteration and prevent false negatives from network volatility.
- Tradeoff: fixture tests must be updated when site markup meaningfully changes.

### Results
- Output: resilient discovery + extraction path suitable for initial production dry runs.
- Metrics: broader parser-focused test coverage added.
- Quality check: fixture-based assertions verify key fields extraction end-to-end.

### Challenges
- Needed balanced parsing that is tolerant to markup variation without overfitting.
- Managed retry policy conservatively to keep compliance-first behavior.

### What I Learned
- A robust scraper is mostly defensive engineering, not just selectors.
- JSON-LD is the highest signal source when available, with title fallbacks for gaps.

### Next Milestone
- Add one-command smoke testing and CI automation for scraper regression checks.

---

## Day 8 - Scraper Test Automation and CI Workflow

### Objective
Make scraper validation repeatable with one local command and automated CI checks.

### Actions Taken
- Added `scripts/test_scraper_pipeline.py` to run:
  - unit tests
  - sample dry-run ingestion
  - optional live dry-run ingestion with search URL
- Added GitHub Actions workflows:
  - `.github/workflows/scraper-smoke.yml`
  - `.github/workflows/daily-discovery-dry-run.yml`
- Updated README with scraper smoke-test commands.

### Technical Decisions
- Decision: keep CI workflow dry-run only and DB-independent.
- Reason: stable, low-friction verification in free-tier environments.
- Tradeoff: persistence paths still require optional DB-enabled local tests.

### Results
- Output: scraper pipeline now has repeatable local and CI validation paths.
- Metrics: regression detection capability improved through scheduled dry runs.
- Quality check: workflow definitions and local smoke script align with project commands.

### Challenges
- Needed cross-platform-safe command execution for local smoke testing.
- Kept scheduled dry-run URL configurable but simple for MVP.

### What I Learned
- Early automation dramatically reduces scraper maintenance risk.
- Smoke testing every change is essential for scraper-heavy products.

### Next Milestone
- Execute end-to-end live dry-run and begin v1 scraper “done” validation checklist.

---

## Entry Template

Copy this section for each new day or milestone:

```md
## Day X - [Milestone Name]

### Objective
[What we aimed to do]

### Actions Taken
- 
- 

### Technical Decisions
- Decision:
- Reason:
- Tradeoff:

### Results
- Output:
- Metrics:
- Quality check:

### Challenges
- 
- 

### What I Learned
- 
- 

### Next Milestone
- 
```
