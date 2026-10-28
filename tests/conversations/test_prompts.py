"""Prompt selection and generation linkage without remote credentials."""

from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from app.conversations.llm import LangChainModel
from app.conversations.prompts import LOCAL_PROMPTS, PromptRegistry


@pytest.mark.parametrize("name", list(LOCAL_PROMPTS))
def test_managed_prompt_uses_production_and_five_minute_cache(name):
    calls = []
    managed = SimpleNamespace(
        is_fallback=False, version=7,
        compile=lambda **variables: "Gerenciado " + name,
    )
    client = SimpleNamespace(get_prompt=lambda *args, **kwargs: (calls.append((args, kwargs)), managed)[1])

    resolved = PromptRegistry(client).resolve(name)

    assert resolved.text == "Gerenciado " + name
    assert resolved.metadata == {
        "prompt_name": name, "prompt_version": "7", "prompt_source": "production",
    }
    assert resolved.client_prompt is managed
    assert calls == [((name,), {
        "type": "text", "label": "production", "cache_ttl_seconds": 300,
        "fallback": LOCAL_PROMPTS[name],
    })]


@pytest.mark.parametrize("name", list(LOCAL_PROMPTS))
@pytest.mark.parametrize("failure", ["fallback", "exception"])
def test_local_fallback_for_each_prompt(name, failure):
    remote = SimpleNamespace(is_fallback=True, version=0)

    def get_prompt(*args, **kwargs):
        if failure == "exception":
            raise ConnectionError("unavailable")
        return remote

    resolved = PromptRegistry(SimpleNamespace(get_prompt=get_prompt)).resolve(
        name, now="HOJE", draft="{}", clinic_context="CONTEXTO",
    )
    assert resolved.source == "local"
    assert resolved.version == "local"
    assert resolved.client_prompt is None
    assert "{{" not in resolved.text


def test_langchain_links_only_managed_prompt_to_generation_context(monkeypatch):
    templates = []
    invoked = []
    remote = SimpleNamespace(is_fallback=False, version=3, compile=lambda **kwargs: "Prompt gerenciado")
    registry = PromptRegistry(SimpleNamespace(get_prompt=lambda *args, **kwargs: remote))
    original = ChatPromptTemplate.from_messages

    def template_from_messages(messages):
        template = original(messages)
        templates.append(template)
        return template

    monkeypatch.setattr(ChatPromptTemplate, "from_messages", template_from_messages)

    class FakeModel(RunnableLambda):
        def __init__(self):
            super().__init__(self.reply)

        def with_structured_output(self, schema):
            return self

        def reply(self, prompt_value):
            invoked.append(prompt_value.to_messages())
            return SimpleNamespace(intent="information", content="Resposta")

    model = LangChainModel(prompt_registry=registry)
    model.model = FakeModel()
    messages = [HumanMessage(content="Paciente privado")]
    assert model.classify(messages) == "information"
    assert model.triage(messages) == "Resposta"
    assert len(invoked) == 2
    assert all(template.metadata == {"langfuse_prompt": remote} for template in templates)
    assert all("Paciente privado" not in str(template.metadata) for template in templates)
    assert all(invocation[0].content == "Prompt gerenciado" for invocation in invoked)


def test_langchain_local_fallback_has_no_prompt_link(monkeypatch):
    templates = []
    original = ChatPromptTemplate.from_messages

    def template_from_messages(messages):
        template = original(messages)
        templates.append(template)
        return template

    monkeypatch.setattr(ChatPromptTemplate, "from_messages", template_from_messages)
    registry = PromptRegistry(SimpleNamespace(get_prompt=lambda *args, **kwargs: SimpleNamespace(is_fallback=True)))
    model = LangChainModel(prompt_registry=registry)
    model.model = RunnableLambda(lambda prompt: SimpleNamespace(content="Resposta"))

    assert model.triage([HumanMessage(content="Paciente privado")]) == "Resposta"
    assert templates[0].metadata is None
