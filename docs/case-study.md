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
