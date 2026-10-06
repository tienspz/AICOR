"""
Tests for Task BE-05: FastAPI REST service (offline-safe).
"""
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["system"] == "AICOR"


def test_facts_and_filter():
    resp = client.get("/api/facts")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 54
    resp2 = client.get("/api/facts", params={"company_id": 1, "quarter": "2024-Q1"})
    body = resp2.json()
    assert resp2.status_code == 200
    assert body["count"] >= 1
    assert all(f["company_id"] == 1 for f in body["facts"])


def test_events_and_sensitivity():
    events = client.get("/api/events").json()
    assert events["count"] >= 1
    sens = client.get("/api/sensitivity").json()
    assert sens["count"] >= 1


def test_stock_live_structure():
    body = client.get("/api/stock/msft/live").json()
    assert body["symbol"] == "MSFT"
    assert body["latency_minutes"] == 15
    assert "Yahoo" in body["source"]


def test_simulate_portfolio_valid_and_invalid():
    ok = client.post(
        "/api/simulate-portfolio",
        json={"weights": {"MSFT": 0.4, "OpenAI": 0.4, "Anthropic": 0.2}},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert "portfolio_score" in body
    assert "không phải khuyến nghị đầu tư" in body["disclaimer"]

    bad = client.post(
        "/api/simulate-portfolio",
        json={"weights": {"MSFT": 0.5, "OpenAI": 0.5, "Anthropic": 0.5}},
    )
    assert bad.status_code == 422
