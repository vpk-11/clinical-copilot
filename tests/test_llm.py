import pytest

import shared.llm as llm
from agents import risk
from agents.ingestion import run as ingest

ING = ingest("VITALS:\nHR 120, SpO2 90% on RA\n" + "x" * 50)
MED = {"agent": "medication", "payload": {"medications": [], "interactions": []}}


def _fake_completion(monkeypatch, outcomes):
    """outcomes: list of exceptions to raise or (content, finish_reason) tuples to return."""
    calls = []

    def fake(**kwargs):
        calls.append(kwargs)
        out = outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        content, finish = out
        msg = type("M", (), {"content": content})()
        choice = type("C", (), {"message": msg, "finish_reason": finish})()
        return type("R", (), {"choices": [choice], "usage": None})()

    monkeypatch.setattr(llm, "_litellm_completion", fake)
    monkeypatch.setattr(llm, "_OBS_AVAILABLE", False)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    return calls


def _named(name):
    return type(name, (Exception,), {})("boom")


def test_no_per_model_params(monkeypatch):
    calls = _fake_completion(monkeypatch, [("{}", "stop")])
    llm.chat("x", model="groq/openai/gpt-oss-20b")
    assert set(calls[0]) == {"model", "messages", "max_tokens"}


def test_truncation_raises_only_when_asked(monkeypatch):
    _fake_completion(monkeypatch, [("", "length"), ("", "length")])
    assert llm.chat("x", model="m") == ""
    with pytest.raises(llm.LLMTruncated):
        llm.chat("x", model="m", fail_on_truncation=True)


def test_transient_error_backs_off_then_succeeds(monkeypatch):
    calls = _fake_completion(monkeypatch, [_named("RateLimitError"), _named("Timeout"), ("{}", "stop")])
    assert llm.chat("x", model="m") == "{}"
    assert len(calls) == 3


@pytest.mark.parametrize("msg,expected", [
    ("Rate limit. Please try again in 7.14s. Need more", 7.64),
    ("try again in 350ms", 0.85),
    ("try again in 1m5.2s", 30),
    ("no hint here", 5),
])
def test_retry_delay_reads_provider_hint(msg, expected):
    assert llm.retry_delay(Exception(msg), 0) == pytest.approx(expected)


def test_auth_error_fails_fast(monkeypatch):
    calls = _fake_completion(monkeypatch, [_named("AuthenticationError"), ("{}", "stop")])
    with pytest.raises(Exception):
        llm.chat("x", model="m")
    assert len(calls) == 1


def test_truncated_output_is_rerun_with_double_tokens(monkeypatch):
    calls = _fake_completion(monkeypatch, [("", "length"), ('{"flags": []}', "stop")])
    msg = risk.run(ING, MED, "t")
    assert msg["status"] == "ok"
    assert [c["max_tokens"] for c in calls] == [llm.DEFAULT_MAX_TOKENS, llm.DEFAULT_MAX_TOKENS * 2]


def test_persistent_truncation_degrades_with_reason(monkeypatch):
    _fake_completion(monkeypatch, [("", "length"), ("", "length")])
    msg = risk.run(ING, MED, "t")
    assert msg["status"] == "degraded" and msg["payload"]["reason"] == "truncated"
