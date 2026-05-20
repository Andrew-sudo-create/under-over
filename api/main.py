from fastapi import FastAPI

from api.config import settings


app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.env}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "under-over API is running"}
