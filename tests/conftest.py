import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["WANDB_ENABLED"] = "false"
os.environ.pop("API_KEY", None)

import pytest


class StubLLM:
    """Replaces shared.llm.chat in every module that imported it."""

    def __init__(self):
        self.response = '{"soap_note": {"subjective": "s", "objective": "o", "assessment": "a", "plan": "p"}, "summary": "sum", "red_flags": []}'
        self.error: Exception | None = None

    def __call__(self, prompt, *args, **kwargs):
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def stub_llm(monkeypatch):
    stub = StubLLM()
    import shared.llm
    from agents import input as input_agent, medication, risk, synthesis, timeline
    from shared import reports
    for mod in (shared.llm, input_agent, medication, reports, risk, synthesis, timeline):
        monkeypatch.setattr(mod, "chat", stub)
    return stub


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """OpenFDA lookups time out by default; tests never touch the network."""
    import requests
    from agents import medication

    def _timeout(*a, **k):
        raise requests.Timeout()

    monkeypatch.setattr(medication.requests, "get", _timeout)
