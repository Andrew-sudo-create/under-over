from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import psycopg

from api.config import settings
from db.persistence import persist_listing
from scraper.base import ListingAdapter
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
                    if conn:
                        persist_listing(conn, raw, normalized)
                        conn.commit()
                        written_count += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"listing_failed: {listing_url} -> {exc}")
    finally:
        if conn:
            conn.close()

    finished_at = datetime.now(timezone.utc)
    return IngestionResult(
        source=adapter.source_name,
        mode="sample" if sample_mode else "live",
        started_at=started_at,
        finished_at=finished_at,
        search_url=search_url,
        discovered_count=len(discovered_urls),
        processed_count=processed_count,
        written_count=written_count,
        errors=errors,
    )
