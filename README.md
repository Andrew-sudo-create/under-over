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

## Day 1 quickstart

1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Run tests:
   - `python -m pytest -q`
3. Run API:
   - `python -m uvicorn api.main:app --reload`

Health endpoint:

- `GET /health`
