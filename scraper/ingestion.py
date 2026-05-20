from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import psycopg

from api.config import settings
from db.ingestion_runs import save_ingestion_run
from db.persistence import persist_listing
from scraper.base import ListingAdapter, NormalizedListing
from scraper.sample_data import sample_raw_listing


@dataclass(slots=True)
class IngestionResult:
    source: str
    mode: str
    started_at: datetime
    finished_at: datetime
    search_url: str | None
    discovered_count: int
    processed_count: int
    written_count: int
    errors: list[str]
    quality_summary: dict[str, int | float]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["started_at"] = self.started_at.isoformat()
        payload["finished_at"] = self.finished_at.isoformat()
        return payload


def run_ingestion(
    adapter: ListingAdapter,
    *,
    search_url: str | None = None,
    limit: int = 5,
    write_to_db: bool = False,
    sample_mode: bool = False,
) -> IngestionResult:
    started_at = datetime.now(timezone.utc)
    errors: list[str] = []
    processed_count = 0
    written_count = 0
    discovered_urls: list[str] = []
    normalized_records: list[NormalizedListing] = []

    if sample_mode:
        discovered_urls = [sample_raw_listing().listing_url]
    elif search_url:
        try:
            discovered_urls = adapter.discover_listing_urls(search_url, limit=limit)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"discovery_failed: {exc}")

    if write_to_db:
        conn = psycopg.connect(settings.database_url)
    else:
        conn = None

    try:
        if sample_mode:
            raw = sample_raw_listing()
            normalized = adapter.normalize_listing(raw)
            processed_count += 1
            normalized_records.append(normalized)
            if conn:
                persist_listing(conn, raw, normalized)
                conn.commit()
                written_count += 1
        else:
            for listing_url in discovered_urls:
                try:
                    raw = adapter.fetch_listing(listing_url)
                    normalized = adapter.normalize_listing(raw)
                    processed_count += 1
                    normalized_records.append(normalized)
                    if conn:
                        persist_listing(conn, raw, normalized)
                        conn.commit()
                        written_count += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"listing_failed: {listing_url} -> {exc}")

        quality_summary = _build_quality_summary(
            discovered_urls=discovered_urls,
            normalized_records=normalized_records,
            errors=errors,
        )

        finished_at = datetime.now(timezone.utc)
        result = IngestionResult(
            source=adapter.source_name,
            mode="sample" if sample_mode else "live",
            started_at=started_at,
            finished_at=finished_at,
            search_url=search_url,
            discovered_count=len(discovered_urls),
            processed_count=processed_count,
            written_count=written_count,
            errors=errors,
            quality_summary=quality_summary,
        )

        if conn is not None:
            save_ingestion_run(conn, result)
            conn.commit()

        return result
    finally:
        if conn is not None and not conn.closed:
            conn.close()


def _build_quality_summary(
    *,
    discovered_urls: list[str],
    normalized_records: list[NormalizedListing],
    errors: list[str],
) -> dict[str, int | float]:
    unique_discovered_count = len(set(discovered_urls))
    duplicate_url_count = len(discovered_urls) - unique_discovered_count
    missing_city_count = sum(1 for row in normalized_records if not row.city)
    missing_suburb_count = sum(1 for row in normalized_records if not row.suburb)
    missing_property_type_count = sum(1 for row in normalized_records if not row.property_type)
    missing_asking_price_count = sum(1 for row in normalized_records if row.asking_price is None)
    missing_critical_count = sum(
        1
        for row in normalized_records
        if (row.asking_price is None or not row.city or not row.suburb or not row.property_type)
    )
    parse_failure_count = sum(1 for entry in errors if entry.startswith("listing_failed:"))

    return {
        "discovered_count": len(discovered_urls),
        "unique_discovered_count": unique_discovered_count,
        "duplicate_url_count": duplicate_url_count,
        "processed_count": len(normalized_records),
        "error_count": len(errors),
        "parse_failure_count": parse_failure_count,
        "missing_city_count": missing_city_count,
        "missing_suburb_count": missing_suburb_count,
        "missing_property_type_count": missing_property_type_count,
        "missing_asking_price_count": missing_asking_price_count,
        "missing_critical_count": missing_critical_count,
    }
