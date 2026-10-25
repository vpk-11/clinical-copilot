import json

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


def _events(resp):
    out = []
    for block in resp.text.strip().split("\n\n"):
        name, data = block.split("\n", 1)
        out.append((name.removeprefix("event: "), json.loads(data.removeprefix("data: "))))
    return out


def test_stream_event_order_and_final_payload_matches_analyze(client):
    streamed = _events(client.post("/analyze/stream", json=BODY))
    names = [(n, d.get("agent")) for n, d in streamed]
    assert names[0] == ("agent_started", "ingestion")
    finished = [d["agent"] for n, d in streamed if n == "agent_finished"]
    assert finished[0] == "ingestion"
    assert set(finished[1:3]) == {"medication", "timeline"}
    assert finished[3:] == ["risk", "synthesis"]
    assert streamed[-1][0] == "pipeline_done"
    plain = client.post("/analyze", json=BODY).json()
    assert streamed[-1][1].keys() == plain.keys()


def test_stream_requires_api_key_and_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(main, "_API_KEY", "secret")
    assert client.post("/analyze/stream", json=BODY).status_code == 401
    monkeypatch.setattr(main, "_API_KEY", None)
    codes = [client.post("/analyze/stream", json=BODY).status_code for _ in range(11)]
    assert codes[-1] == 429
