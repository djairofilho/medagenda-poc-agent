"""Deterministic model used by local evals and tests; never used for live chat."""

import re

from app.conversations.llm import AppointmentExtraction


class FakeModel:
    model_name = "fake-model"

    def classify(self, messages, config=None) -> str:
        text = str(messages[-1].content).lower()
        if any(word in text for word in ("endereço", "convenio", "convênio", "onde fica")):
            return "information"
        if any(word in text for word in ("dor", "febre", "diagnóstico", "remédio")):
            return "triage"
        return "scheduling"

    def extract(self, message: str, draft: dict, config=None) -> AppointmentExtraction:
        data = {}
        specialty = re.search(r"\b(cardiologia|dermatologia|pediatria)\b", message, re.I)
        if specialty:
            data["specialty"] = specialty.group(1).capitalize()
        when = re.search(r"\b(20\d{2}-\d{2}-\d{2})[ T](\d{2}:\d{2})\b", message)
        if when:
            data["datetime_iso"] = f"{when.group(1)}T{when.group(2)}:00-03:00"
        name = re.search(r"nome:\s*([A-Za-zÀ-ÿ ]+?)(?=\s+(?:cpf|telefone|presencial|teleconsulta)\b|$)", message, re.I)
        if name:
            data["name"] = name.group(1).strip()
        cpf = re.search(r"cpf:?\s*([\d.\-]{11,14})", message, re.I)
        if cpf:
            data["cpf"] = cpf.group(1)
        phone = re.search(r"telefone:?\s*([\d()\s\-]{10,20})", message, re.I)
        if phone:
            data["phone"] = phone.group(1).strip()
        if "teleconsulta" in message.lower():
            data["mode"] = "teleconsulta"
        elif "presencial" in message.lower():
            data["mode"] = "presencial"
        lowered = message.strip().lower()
        data["confirmation"] = "yes" if lowered in ("sim", "confirmo") else "no" if lowered == "não" else "unknown"
        return AppointmentExtraction(**data)

    def information(self, messages, session_factory, config=None) -> str:
        return "A clínica fica na Av. Paulista, 1000, em São Paulo."

    def triage(self, messages, config=None) -> str:
        return "Não posso avaliar sintomas ou dar diagnóstico. Deseja agendar uma consulta?"
