# Scraping Compliance Rules (Day 2)

`under-over` follows a compliance-first approach for data collection.

## Rules

1. Always check `robots.txt` before scraping a page.
2. Use conservative request pacing with random jitter.
3. Use transparent user-agent identification for production.
4. Fail closed when robots checks cannot be completed.
5. Start with the smallest useful crawl scope (single region/source).
6. Prefer official/licensed feeds when available.

## Current implementation status

- `scraper.compliance.ComplianceGuard` handles:
  - robots checks
  - jittered delay
  - HTTP client construction with declared user-agent
- `scraper.property24.Property24Adapter` calls compliance guard before requests.

## Non-goals for v1

- CAPTCHA solving
- aggressive anti-bot bypass behavior
- high-volume distributed crawling
