import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from app import config
from app.conversations.codex_cli import CodexCliModel
from app.conversations.prompts import PromptRegistry


def test_codex_cli_uses_structured_output_without_exposing_app_keys(monkeypatch):
    replies = iter([
        {"intent": "scheduling"},
        {"specialty": "Cardiologia", "datetime_iso": None, "name": None,
         "cpf": None, "phone": None, "mode": None, "confirmation": "unknown"},
    ])
    commands = []

    def fake_run(command, *, input, env, **kwargs):
        commands.append(command)
        assert "--ephemeral" in command and "read-only" in command
        assert command[command.index("--model") + 1] == "gpt-6-luna"
        assert command[command.index("--config") + 1] == "model_reasoning_effort=low"
        assert "DATABASE_URL" not in env and "LANGFUSE_SECRET_KEY" not in env
        assert kwargs["timeout"] == 120
        Path(command[command.index("-o") + 1]).write_text(json.dumps(next(replies)), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("shutil.which", lambda _: "codex")
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(config, "CODEX_MODEL", "gpt-6-luna")
    monkeypatch.setattr(config, "CODEX_REASONING_EFFORT", "low")
    monkeypatch.setenv("DATABASE_URL", "private-db-url")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "private-key")
    model = CodexCliModel()

    assert model.classify([HumanMessage(content="Quero agendar Cardiologia")]) == "scheduling"
    extracted = model.extract("Quero agendar Cardiologia", {})
    assert extracted.specialty == "Cardiologia"
    assert len(commands) == 2
    assert all("--output-schema" in command for command in commands)


def test_codex_generation_links_managed_prompt_without_text_metadata(monkeypatch):
    calls = []
    managed = SimpleNamespace(is_fallback=False, version=2, compile=lambda **kwargs: "Instrução gerenciada")
    registry = PromptRegistry(SimpleNamespace(get_prompt=lambda *args, **kwargs: managed))

    def start_observation(**kwargs):
        calls.append(kwargs)
        return nullcontext()

    def fake_run(command, *, input, **kwargs):
        assert "Instrução gerenciada" in input
        assert "segredo do paciente" in input
        Path(command[command.index("-o") + 1]).write_text("Resposta", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("shutil.which", lambda _: "codex")
    monkeypatch.setattr("subprocess.run", fake_run)
    model = CodexCliModel(
        tracer=SimpleNamespace(client=SimpleNamespace(start_as_current_observation=start_observation)),
        prompt_registry=registry,
    )
    assert model.triage([HumanMessage(content="segredo do paciente")]) == "Resposta"
    assert calls == [{
        "as_type": "generation", "name": "codex-cli-triage", "model": model.model_name,
        "metadata": {"prompt_name": "triage", "prompt_version": "2", "prompt_source": "production"},
        "prompt": managed,
    }]
    assert "segredo do paciente" not in str(calls)
