# MVP Scope (Day 1)

This is the initial build scope for `under-over` so we can execute quickly and avoid early rework.

## Current defaults

- Region: Gauteng
- Property type: Apartments
- Primary source: Property24
- Operating mode: Compliance-first data collection
- Stack:
  - Backend: FastAPI (Python)
  - Database: PostgreSQL
  - Frontend: Next.js (to be added in product phase)

## v1 user flow target

1. User submits a listing URL (and later optional manual form).
2. App fetches normalized listing data from DB.
3. Model predicts fair value and confidence.
4. App classifies listing: undervalued, fair, or overvalued.
5. App displays comparable evidence and market snapshot.

## v1 success criteria

- Ingestion pipeline runs on schedule without manual intervention.
- Data model supports historical price tracking.
- API has stable health endpoint and valuation endpoint scaffold.
- Baseline tests pass in CI/local workflow.
