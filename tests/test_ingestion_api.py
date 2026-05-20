from fastapi.testclient import TestClient

from api import main


client = TestClient(main.app)


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


def test_ingestion_trends_endpoint_with_mocked_runs(monkeypatch) -> None:
    sample_runs = [{"id": 1, "source": "property24", "mode": "sample"}]
    monkeypatch.setattr(main, "get_recent_ingestion_runs", lambda *_args, **_kwargs: sample_runs)

    response = client.get("/api/v1/ingestion/trends?limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["runs"][0]["source"] == "property24"


def test_data_quality_report_endpoint_with_mocked_report(monkeypatch) -> None:
    fake_report = {
        "total_rows": 2,
        "missing_rates": {"city_pct": 0.0},
        "counts": {"missing_city_count": 0},
        "by_city": [{"city": "Johannesburg", "listing_count": 2, "missing_price_count": 0}],
    }
    monkeypatch.setattr(main, "get_data_quality_report", lambda *_args, **_kwargs: fake_report)

    response = client.get("/api/v1/data-quality/report")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["report"]["total_rows"] == 2
