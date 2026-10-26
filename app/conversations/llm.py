"""Structured model boundary; tests and evals replace this adapter."""

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app import config
from app.clinic.service import clinic_context


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
    def __init__(self):
        self.model = None
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

    def classify(self, messages, config=None) -> str:
        result = self._get_model().with_structured_output(IntentDecision).invoke(
            [SystemMessage(content=(
                "Classifique a intenção atual: agendamento, dúvida administrativa ou sintomas/pedido médico. "
                "Se houver sintomas, use triage. Responda apenas no esquema solicitado."
            ))] + messages[-8:], config=config
        )
        return result.intent

    def extract(self, message: str, draft: dict, config=None) -> AppointmentExtraction:
        now = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        result = self._get_model().with_structured_output(AppointmentExtraction).invoke(
            [SystemMessage(content=(
                f"Extraia apenas dados expressos nesta mensagem para agendamento. Agora: {now}. "
                "Converta datas relativas somente se dia e hora forem explícitos. "
                "Não invente campos ausentes. 'sim/confirmo' é yes; 'não/cancelar' é no. "
                f"Dados já coletados (só contexto): { {k: v for k, v in draft.items() if k not in ('cpf', 'phone')} }"
            )), HumanMessage(content=message)], config=config
        )
        return result

    def information(self, messages, session_factory, config=None) -> str:
        response = self._get_model().invoke(
            [SystemMessage(content=(
                "Responda brevemente em português somente com base nas informações abaixo. "
                "Se faltar informação, sugira falar com a recepção.\n" + clinic_context(session_factory)
            ))] + messages[-8:], config=config
        )
        return str(response.content)

    def triage(self, messages, config=None) -> str:
        response = self._get_model().invoke(
            [SystemMessage(content=(
                "Não dê diagnóstico nem tratamento. Diga que a dúvida clínica precisa de avaliação médica "
                "e pergunte se a pessoa deseja agendar uma consulta. Responda em português de forma breve."
            ))] + messages[-8:], config=config
        )
        return str(response.content)
