import json
from pathlib import Path
from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from app import config
from app.conversations.codex_cli import CodexCliModel


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
        assert "DATABASE_URL" not in env and "LANGFUSE_SECRET_KEY" not in env
        assert kwargs["timeout"] == 120
        Path(command[command.index("-o") + 1]).write_text(json.dumps(next(replies)), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("shutil.which", lambda _: "codex")
    monkeypatch.setattr("subprocess.run", fake_run)
    monkeypatch.setattr(config, "CODEX_MODEL", None)
    monkeypatch.setenv("DATABASE_URL", "private-db-url")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "private-key")
    model = CodexCliModel()

    assert model.classify([HumanMessage(content="Quero agendar Cardiologia")]) == "scheduling"
    extracted = model.extract("Quero agendar Cardiologia", {})
    assert extracted.specialty == "Cardiologia"
    assert len(commands) == 2
    assert all("--output-schema" in command for command in commands)
