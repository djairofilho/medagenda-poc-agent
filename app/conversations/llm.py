"""Structured model boundary; tests and evals replace this adapter."""

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from app import config
from app.clinic.service import clinic_context
from app.conversations.prompts import PromptRegistry


class IntentDecision(BaseModel):
    intent: Literal["scheduling", "triage", "information"]


class AppointmentExtraction(BaseModel):
    specialty: str | None = None
    datetime_iso: str | None = Field(default=None, description="Explicit requested date and time as ISO 8601 with -03:00 offset")
    name: str | None = None
    cpf: str | None = None
    phone: str | None = None
    mode: Literal["presencial", "teleconsulta"] | None = None
    confirmation: Literal["yes", "no", "unknown"] = "unknown"


class LangChainModel:
    def __init__(self, tracer=None, prompt_registry=None):
        self.model = None
        self.tracer = tracer
        self.prompt_registry = prompt_registry
        self.model_name = config.OPENAI_MODEL if config.LLM_PROVIDER == "openai" else config.GEMINI_MODEL

    def _get_model(self):
        if self.model is not None:
            return self.model
        if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
            from langchain_openai import ChatOpenAI

            self.model = ChatOpenAI(model=config.OPENAI_MODEL, api_key=config.OPENAI_API_KEY, max_retries=2)
        elif config.LLM_PROVIDER == "gemini" and config.GOOGLE_API_KEY:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self.model = ChatGoogleGenerativeAI(model=config.GEMINI_MODEL, google_api_key=config.GOOGLE_API_KEY, max_retries=2)
        else:
            raise RuntimeError("Configure LLM_PROVIDER and a matching API key before calling /chat")
        return self.model

    def _prompts(self):
        if self.prompt_registry is None:
            self.prompt_registry = PromptRegistry(self.tracer.client if self.tracer else None)
        return self.prompt_registry

    @staticmethod
    def _invoke(model, messages, prompt, run_config):
        # Langfuse's LangChain callback registers the prompt on the template run
        # and links it to the child generation. Never put text in metadata.
        template = ChatPromptTemplate.from_messages([
            SystemMessage(content=prompt.text), MessagesPlaceholder("history"),
        ])
        if prompt.client_prompt is not None:
            template.metadata = {"langfuse_prompt": prompt.client_prompt}
        chain_config = dict(run_config or {})
        chain_config["metadata"] = {**(chain_config.get("metadata") or {}), **prompt.metadata}
        return (template | model).invoke({"history": messages}, config=chain_config)

    def classify(self, messages, config=None) -> str:
        prompt = self._prompts().resolve("classification")
        result = self._invoke(
            self._get_model().with_structured_output(IntentDecision),
            messages[-8:], prompt, config,
        )
        return result.intent

    def extract(self, message: str, draft: dict, config=None) -> AppointmentExtraction:
        now = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        context = {key: value for key, value in draft.items() if key not in ("cpf", "phone")}
        prompt = self._prompts().resolve("extraction", now=now, draft=str(context))
        return self._invoke(
            self._get_model().with_structured_output(AppointmentExtraction),
            [HumanMessage(content=message)], prompt, config,
        )

    def information(self, messages, session_factory, config=None) -> str:
        prompt = self._prompts().resolve("information", clinic_context=clinic_context(session_factory))
        response = self._invoke(
            self._get_model(), messages[-8:], prompt, config,
        )
        return str(response.content)

    def triage(self, messages, config=None) -> str:
        prompt = self._prompts().resolve("triage")
        response = self._invoke(
            self._get_model(), messages[-8:], prompt, config,
        )
        return str(response.content)
