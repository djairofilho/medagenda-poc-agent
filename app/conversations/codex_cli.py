"""Local POC model adapter using the authenticated Codex CLI."""

import json
import os
import shutil
import subprocess
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo

from app import config
from app.clinic.service import clinic_context
from app.conversations.llm import AppointmentExtraction
from app.conversations.prompts import PromptRegistry, ResolvedPrompt


INTENT_SCHEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": ["scheduling", "triage", "information"]}},
    "required": ["intent"],
    "additionalProperties": False,
}
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        field: {"type": ["string", "null"]}
        for field in ("specialty", "datetime_iso", "name", "cpf", "phone")
    } | {
        "mode": {"type": ["string", "null"], "enum": ["presencial", "teleconsulta", None]},
        "confirmation": {"type": "string", "enum": ["yes", "no", "unknown"]},
    },
    "required": ["specialty", "datetime_iso", "name", "cpf", "phone", "mode", "confirmation"],
    "additionalProperties": False,
}


class CodexCliModel:
    def __init__(self, tracer=None, prompt_registry=None):
        self.codex = shutil.which("codex")
        if not self.codex:
            raise RuntimeError("Codex CLI não encontrado no PATH")
        self.tracer = tracer
        self.prompt_registry = prompt_registry
        self.model_name = config.CODEX_MODEL or "codex-cli-default"

    def _prompts(self):
        if self.prompt_registry is None:
            self.prompt_registry = PromptRegistry(self.tracer.client if self.tracer else None)
        return self.prompt_registry

    def _call(self, operation: str, prompt: ResolvedPrompt, user_input: str,
              schema: dict | None = None):
        with TemporaryDirectory(prefix="medagenda_codex_") as directory:
            path = Path(directory)
            answer_path = path / "answer.txt"
            command = [
                self.codex, "--ask-for-approval", "never", "exec", "--ephemeral",
                "--ignore-user-config", "--skip-git-repo-check", "--sandbox", "read-only",
                "-C", directory, "-o", str(answer_path),
            ]
            if config.CODEX_MODEL:
                command.extend(["--model", config.CODEX_MODEL])
            if config.CODEX_REASONING_EFFORT:
                command.extend(["--config", f"model_reasoning_effort={config.CODEX_REASONING_EFFORT}"])
            if schema is not None:
                schema_path = path / "schema.json"
                schema_path.write_text(json.dumps(schema), encoding="utf-8")
                command.extend(["--output-schema", str(schema_path)])
            command.append("-")
            kwargs = {
                "as_type": "generation", "name": f"codex-cli-{operation}",
                "model": self.model_name, "metadata": prompt.metadata,
            }
            if prompt.client_prompt is not None:
                kwargs["prompt"] = prompt.client_prompt
            span = self.tracer.client.start_as_current_observation(**kwargs) if self.tracer else nullcontext()
            # Keep application credentials out of the subprocess environment.
            child_env = os.environ.copy()
            for key in ("DATABASE_URL", "CHECKPOINT_DATABASE_URL", "LANGFUSE_PUBLIC_KEY",
                        "LANGFUSE_SECRET_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
                child_env.pop(key, None)
            try:
                with span:
                    # One CLI process per step; use an API provider when latency matters.
                    result = subprocess.run(
                        command, input=prompt.text + "\n" + user_input,
                        text=True, encoding="utf-8", errors="replace",
                        capture_output=True, timeout=120, check=False, env=child_env,
                    )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Codex timeout") from exc
            if result.returncode:
                raise RuntimeError(f"Codex CLI falhou (código {result.returncode})")
            answer = answer_path.read_text(encoding="utf-8").strip()
        return json.loads(answer) if schema is not None else answer

    def classify(self, messages, config=None) -> str:
        history = "\n".join(f"{type(item).__name__}: {item.content}" for item in messages[-8:])
        prompt = self._prompts().resolve("classification")
        return self._call("classify", prompt, history, INTENT_SCHEMA)["intent"]

    def extract(self, message: str, draft: dict, config=None) -> AppointmentExtraction:
        now = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        context = {key: value for key, value in draft.items() if key not in ("cpf", "phone")}
        prompt = self._prompts().resolve("extraction", now=now, draft=str(context))
        result = self._call("extract", prompt, "Mensagem: " + message, EXTRACTION_SCHEMA)
        return AppointmentExtraction.model_validate(result)

    def information(self, messages, session_factory, config=None) -> str:
        prompt = self._prompts().resolve("information", clinic_context=clinic_context(session_factory))
        return self._call("information", prompt, "Pergunta: " + str(messages[-1].content))

    def triage(self, messages, config=None) -> str:
        prompt = self._prompts().resolve("triage")
        return self._call("triage", prompt, str(messages[-1].content))
