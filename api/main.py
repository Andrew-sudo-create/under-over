from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel, Field

from api.config import settings
from scraper.ingestion import run_ingestion
from scraper.property24 import Property24Adapter


app = FastAPI(title=settings.app_name)
_last_ingestion_result: dict | None = None


class IngestionRequest(BaseModel):
    search_url: str | None = None
    limit: int = Field(default=5, ge=1, le=50)
    write_to_db: bool = False
    sample_mode: bool = False


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

    result = run_ingestion(
        Property24Adapter(),
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
