from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_ingestion_sample_run_endpoint() -> None:
    response = client.post(
        "/api/v1/ingestion/run",
        json={"sample_mode": True, "write_to_db": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["result"]["mode"] == "sample"
    assert payload["result"]["processed_count"] == 1
    assert payload["result"]["quality_summary"]["missing_critical_count"] == 0


def test_ingestion_requires_search_url_for_live_mode() -> None:
    response = client.post(
        "/api/v1/ingestion/run",
        json={"sample_mode": False, "write_to_db": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"


def test_ingestion_summary_endpoint_after_sample_run() -> None:
    client.post(
        "/api/v1/ingestion/run",
        json={"sample_mode": True, "write_to_db": False},
    )
    response = client.get("/api/v1/ingestion/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["summary"]["processed_count"] == 1
