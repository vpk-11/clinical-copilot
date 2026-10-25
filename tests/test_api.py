import pytest
from fastapi.testclient import TestClient

import api.main as main
from api.limiter import limiter

BODY = {"text": "HR 120. " * 10, "patient_id": "T"}


@pytest.fixture
def client(stub_llm):
    limiter.reset()
    return TestClient(main.app)


def test_api_key_required_when_set(client, monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "secret")
    assert client.post("/analyze", json=BODY).status_code == 401
    assert client.post("/analyze", json=BODY, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/analyze", json=BODY, headers={"X-API-Key": "secret"}).status_code == 200


def test_rate_limit_429_on_11th_call(client):
    codes = [client.post("/analyze", json=BODY).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10
    assert codes[10] == 429


def test_cors_rejects_unknown_origin(client):
    ok = client.options("/analyze", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    bad = client.options("/analyze", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


def test_analyze_reports_degraded_with_reason(client, stub_llm):
    stub_llm.error = RuntimeError("boom")
    r = client.post("/analyze", json=BODY).json()
    assert r["pipeline_status"] == "degraded"
    assert "risk: llm_error" in r["pipeline_status_reason"]
