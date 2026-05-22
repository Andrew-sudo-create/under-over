from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from scraper.base import ListingAdapter, NormalizedListing, RawListing
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


ProgressCallback = Callable[[str, dict[str, Any]], None]


def run_ingestion(
    adapter: ListingAdapter,
    *,
    search_url: str | None = None,
    limit: int = 5,
    sample_mode: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> IngestionResult:
    started_at = datetime.now(timezone.utc)
    errors: list[str] = []
    processed_count = 0
    written_count = 0
    discovered_urls: list[str] = []
    normalized_records: list[NormalizedListing] = []
    _notify(
        progress_callback,
        "run_started",
        {
            "adapter": adapter.source_name,
            "search_url": search_url,
            "limit": limit,
            "sample_mode": sample_mode,
            "started_at": started_at.isoformat(),
        },
    )

    if sample_mode:
        discovered_urls = [sample_raw_listing().listing_url]
        _notify(
            progress_callback,
            "discovery_complete",
            {"mode": "sample", "discovered_count": len(discovered_urls)},
        )
    elif search_url:
        try:
            _notify(
                progress_callback,
                "discovery_started",
                {"search_url": search_url, "limit": limit},
            )
            discovered_urls = adapter.discover_listing_urls(search_url, limit=limit)
            _notify(
                progress_callback,
                "discovery_complete",
                {"mode": "live", "discovered_count": len(discovered_urls)},
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"discovery_failed: {exc}")
            _notify(
                progress_callback,
                "discovery_failed",
                {"error": str(exc)},
            )

    if sample_mode:
        raw = sample_raw_listing()
        normalized = adapter.normalize_listing(raw)
        processed_count += 1
        normalized_records.append(normalized)
        _notify(
            progress_callback,
            "listing_processed",
            _listing_log_payload(raw, normalized, processed_count, len(discovered_urls)),
        )
    else:
        for listing_url in discovered_urls:
            try:
                raw = adapter.fetch_listing(listing_url)
                normalized = adapter.normalize_listing(raw)
                processed_count += 1
                normalized_records.append(normalized)
                _notify(
                    progress_callback,
                    "listing_processed",
                    _listing_log_payload(raw, normalized, processed_count, len(discovered_urls)),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"listing_failed: {listing_url} -> {exc}")
                _notify(
                    progress_callback,
                    "listing_failed",
                    {"listing_url": listing_url, "error": str(exc)},
                )

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

    _notify(
        progress_callback,
        "run_finished",
        {
            "source": result.source,
            "mode": result.mode,
            "discovered_count": result.discovered_count,
            "processed_count": result.processed_count,
            "written_count": result.written_count,
            "error_count": len(result.errors),
            "quality_summary": result.quality_summary,
            "finished_at": finished_at.isoformat(),
        },
    )
    return result


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


def _notify(
    callback: ProgressCallback | None,
    event: str,
    payload: dict[str, Any],
) -> None:
    if callback is None:
        return
    callback(event, payload)


def _listing_log_payload(
    raw: RawListing,
    normalized: NormalizedListing,
    processed_count: int,
    total_discovered: int,
) -> dict[str, Any]:
    return {
        "index": processed_count,
        "total_discovered": total_discovered,
        "source_listing_id": raw.source_listing_id,
        "listing_url": raw.listing_url,
        "city": normalized.city,
        "suburb": normalized.suburb,
        "property_type": normalized.property_type,
        "bedrooms": normalized.bedrooms,
        "bathrooms": normalized.bathrooms,
        "parking_spaces": normalized.parking_spaces,
        "asking_price": normalized.asking_price,
        "listed_at": normalized.listed_at.isoformat() if normalized.listed_at else None,
    }
