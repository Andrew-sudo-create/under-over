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
