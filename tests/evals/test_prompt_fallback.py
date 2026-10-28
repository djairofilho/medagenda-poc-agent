"""The four managed prompts remain usable when Langfuse cannot serve production."""

import pytest

from app.conversations.prompts import LOCAL_PROMPTS, PromptRegistry
from app.evals.fake_model import FakeModel
from app.evals.runner import prompt_versions


class ManagedPrompt:
    version = 7
    is_fallback = False

    def compile(self, **variables):
        return "managed:" + ",".join(sorted(variables))


class Client:
    def __init__(self, *, available=True):
        self.available = available
        self.calls = []

    def get_prompt(self, name, **kwargs):
        self.calls.append((name, kwargs))
        if not self.available:
            raise ConnectionError("synthetic outage")
        return ManagedPrompt()


@pytest.mark.parametrize("name", tuple(LOCAL_PROMPTS))
def test_production_prompt_and_local_fallback(name):
    variables = {"now": "2030-01-01", "draft": "{}", "clinic_context": "clínica sintética"}
    client = Client()
    managed = PromptRegistry(client).resolve(name, **variables)
    assert managed.source == "production"
    assert managed.version == "7"
    assert managed.client_prompt is not None
    assert managed.metadata == {
        "prompt_name": name, "prompt_version": "7", "prompt_source": "production",
    }
    assert client.calls == [(name, {
        "type": "text", "label": "production", "cache_ttl_seconds": 300,
        "fallback": LOCAL_PROMPTS[name],
    })]

    local = PromptRegistry(Client(available=False)).resolve(name, **variables)
    assert local.source == "local"
    assert local.version == "local"
    assert local.client_prompt is None
    assert local.text
    assert local.metadata["prompt_source"] == "local"


def test_experiment_prompt_versions_are_controlled():
    assert prompt_versions(FakeModel()) == {name: "local" for name in LOCAL_PROMPTS}
