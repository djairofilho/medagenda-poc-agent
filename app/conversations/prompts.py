"""Versioned system prompts shared by both model adapters.

Only controlled identifiers are exported as trace metadata. Prompt text and
compiled variables remain inside the model call.
"""

from dataclasses import dataclass
from typing import Any, Literal

from app import config


PromptName = Literal["classification", "extraction", "information", "triage"]
PROMPT_CACHE_TTL_SECONDS = 300

LOCAL_PROMPTS: dict[PromptName, str] = {
    "classification": (
        "Classifique a intenção atual: agendamento, dúvida administrativa ou sintomas/pedido médico. "
        "Se houver sintomas, use triage. Responda apenas no esquema solicitado."
    ),
    "extraction": (
        "Extraia apenas dados expressos nesta mensagem para agendamento. Agora: {{now}}. "
        "Converta datas relativas somente se dia e hora forem explícitos. "
        "Não invente campos ausentes. 'sim/confirmo' é yes; 'não/cancelar' é no. "
        "Dados já coletados (só contexto): {{draft}}"
    ),
    "information": (
        "Responda brevemente em português somente com base nas informações abaixo. "
        "Se faltar informação, sugira falar com a recepção.\n{{clinic_context}}"
    ),
    "triage": (
        "Não dê diagnóstico nem tratamento. Diga que a dúvida clínica precisa de avaliação médica "
        "e pergunte se a pessoa deseja agendar uma consulta. Responda em português de forma breve."
    ),
}


def _compile_local(template: str, variables: dict[str, str]) -> str:
    """Use Langfuse's double-brace variable convention without format side effects."""
    result = template
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", value)
    return result


@dataclass(frozen=True)
class ResolvedPrompt:
    name: PromptName
    text: str
    version: str
    source: Literal["production", "local"]
    client_prompt: Any = None

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "prompt_name": self.name,
            "prompt_version": self.version,
            "prompt_source": self.source,
        }


class PromptRegistry:
    def __init__(self, client=None):
        self.client = client

    def _client(self):
        if self.client is not None:
            return self.client
        if not (config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY):
            return None
        from langfuse import Langfuse
        from app.observability.tracing import mask_otel_spans, should_export_span

        self.client = Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            base_url=config.LANGFUSE_BASE_URL,
            mask_otel_spans=mask_otel_spans,
            should_export_span=should_export_span,
        )
        return self.client

    def resolve(self, name: PromptName, **variables: str) -> ResolvedPrompt:
        if name not in LOCAL_PROMPTS:
            raise ValueError("Unknown prompt")
        fallback = LOCAL_PROMPTS[name]
        try:
            client = self._client()
        except Exception:
            client = None
        if client is None:
            return ResolvedPrompt(name, _compile_local(fallback, variables), "local", "local")
        try:
            prompt = client.get_prompt(
                name, type="text", label="production",
                cache_ttl_seconds=PROMPT_CACHE_TTL_SECONDS, fallback=fallback,
            )
            if prompt.is_fallback:
                return ResolvedPrompt(name, _compile_local(fallback, variables), "local", "local")
            version = getattr(prompt, "version", None)
            if not isinstance(version, int) or version < 1:
                raise ValueError("Invalid managed prompt version")
            compiled = prompt.compile(**variables)
            if not isinstance(compiled, str):
                raise ValueError("Invalid managed prompt type")
            return ResolvedPrompt(name, compiled, str(version), "production", prompt)
        except Exception:
            # Langfuse outage or inaccessible production label must not block chat.
            return ResolvedPrompt(name, _compile_local(fallback, variables), "local", "local")
