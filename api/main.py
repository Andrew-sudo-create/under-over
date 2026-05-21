from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.config import settings
from db.ingestion_runs import get_recent_ingestion_runs
from db.quality import get_data_quality_report
from scraper.base import NormalizedListing, RawListing
from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter
from scraper.property24_scrapegraph import Property24ScrapeGraphAdapter


app = FastAPI(title=settings.app_name)
_last_ingestion_result: dict | None = None


class IngestionRequest(BaseModel):
    search_url: str | None = None
    limit: int = Field(default=5, ge=1, le=50)
    write_to_db: bool = False
    sample_mode: bool = False
    backend: str = Field(default="html")


class DiscoverRequest(BaseModel):
    search_url: str
    limit: int = Field(default=5, ge=1, le=50)
    backend: str = Field(default="html")


class ListingRequest(BaseModel):
    listing_url: str
    backend: str = Field(default="html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.env}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "under-over API is running"}


@app.post(f"{settings.api_prefix}/ingestion/run")
def ingestion_run(payload: IngestionRequest) -> dict:
    global _last_ingestion_result

    if not payload.sample_mode and not payload.search_url:
        return {
            "status": "error",
            "message": "search_url is required unless sample_mode=true",
        }

    try:
        adapter = _build_adapter(payload.backend)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    result = run_ingestion(
        adapter,
        search_url=payload.search_url,
        limit=payload.limit,
        write_to_db=payload.write_to_db,
        sample_mode=payload.sample_mode,
    )
    _last_ingestion_result = result.to_dict()
    return {"status": "ok", "result": _last_ingestion_result}


@app.get(f"{settings.api_prefix}/ingestion/status")
def ingestion_status() -> dict:
    if _last_ingestion_result is None:
        return {
            "status": "idle",
            "last_run": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    return {
        "status": "ready",
        "last_run": _last_ingestion_result,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get(f"{settings.api_prefix}/ingestion/summary")
def ingestion_summary() -> dict:
    if _last_ingestion_result is None:
        return {
            "status": "idle",
            "summary": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    return {
        "status": "ready",
        "summary": _last_ingestion_result.get("quality_summary"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get(f"{settings.api_prefix}/ingestion/trends")
def ingestion_trends(limit: int = 10) -> dict:
    safe_limit = min(max(limit, 1), 100)
    try:
        runs = get_recent_ingestion_runs(settings.database_url, limit=safe_limit)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"failed_to_load_trends: {exc}",
            "runs": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "status": "ok",
        "runs": runs,
        "count": len(runs),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get(f"{settings.api_prefix}/data-quality/report")
def data_quality_report() -> dict:
    try:
        report = get_data_quality_report(settings.database_url)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"failed_to_build_report: {exc}",
            "report": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    return {
        "status": "ok",
        "report": report,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post(f"{settings.api_prefix}/scraper/discover")
def scraper_discover(payload: DiscoverRequest) -> dict:
    try:
        adapter = _build_adapter(payload.backend)
        urls = adapter.discover_listing_urls(payload.search_url, limit=payload.limit)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"discover_failed: {exc}",
            "urls": [],
        }

    return {
        "status": "ok",
        "source": adapter.source_name,
        "search_url": payload.search_url,
        "count": len(urls),
        "urls": urls,
    }


@app.post(f"{settings.api_prefix}/scraper/fetch")
def scraper_fetch(payload: ListingRequest) -> dict:
    try:
        adapter = _build_adapter(payload.backend)
        raw = adapter.fetch_listing(payload.listing_url)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"fetch_failed: {exc}",
            "raw": None,
        }
    return {
        "status": "ok",
        "source": adapter.source_name,
        "raw": _serialize_raw_listing(raw),
    }


@app.post(f"{settings.api_prefix}/scraper/normalize")
def scraper_normalize(payload: ListingRequest) -> dict:
    try:
        adapter = _build_adapter(payload.backend)
        raw = adapter.fetch_listing(payload.listing_url)
        normalized = adapter.normalize_listing(raw)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"normalize_failed: {exc}",
            "normalized": None,
        }

    missing_fields = _critical_missing_fields(normalized)
    return {
        "status": "ok",
        "source": adapter.source_name,
        "raw": _serialize_raw_listing(raw),
        "normalized": _serialize_normalized_listing(normalized),
        "missing_critical_fields": missing_fields,
    }


def _serialize_raw_listing(raw: RawListing) -> dict:
    payload = asdict(raw)
    payload["scraped_at"] = raw.scraped_at.isoformat()
    return payload


def _serialize_normalized_listing(listing: NormalizedListing) -> dict:
    payload = asdict(listing)
    for key in ("listed_at", "first_seen_at", "last_seen_at"):
        value = payload.get(key)
        if value is not None:
            payload[key] = value.isoformat()
    return payload


def _critical_missing_fields(listing: NormalizedListing) -> list[str]:
    missing: list[str] = []
    if listing.asking_price is None:
        missing.append("asking_price")
    if not listing.city:
        missing.append("city")
    if not listing.suburb:
        missing.append("suburb")
    if not listing.property_type:
        missing.append("property_type")
    return missing


def _build_adapter(backend: str) -> Property24Adapter:
    normalized = backend.strip().lower()
    if normalized in {"html", "http"}:
        return Property24Adapter()
    if normalized in {"scrapegraph", "sg"}:
        return Property24ScrapeGraphAdapter()
    raise ValueError(f"unsupported backend: {backend}. Expected one of: html, scrapegraph.")
