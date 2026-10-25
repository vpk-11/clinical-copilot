import shared.llm as llm


def _capture(monkeypatch):
    seen = {}

    def fake(**kwargs):
        seen.update(kwargs)
        msg = type("M", (), {"content": "{}"})()
        return type("R", (), {"choices": [type("C", (), {"message": msg})()], "usage": None})()

    monkeypatch.setattr(llm, "_litellm_completion", fake)
    monkeypatch.setattr(llm, "_OBS_AVAILABLE", False)
    return seen


def test_gpt_oss_gets_low_reasoning_effort(monkeypatch):
    seen = _capture(monkeypatch)
    llm.chat("x", model="groq/openai/gpt-oss-20b")
    assert seen["reasoning_effort"] == "low"


def test_other_models_get_no_reasoning_effort(monkeypatch):
    seen = _capture(monkeypatch)
    llm.chat("x", model="ollama/qwen2.5:7b")
    assert "reasoning_effort" not in seen
