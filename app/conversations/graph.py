"""One LangGraph turn per request, with durable state between turns."""

from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from app.appointments.service import book_appointment
from app.availability.service import LOCAL_TZ, display_slot_datetime, list_slots
from app.conversations.safety import EMERGENCY_REPLY, is_emergency
from app.conversations.state import ConversationState
from app.patients.service import digits, valid_cpf, valid_phone


def _last_human(state: ConversationState) -> str:
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def _affirmative(text: str) -> bool:
    return text.strip().lower() in {"sim", "confirmo", "sim, confirmo", "ok", "pode confirmar"}


def _negative(text: str) -> bool:
    return text.strip().lower() in {"não", "nao", "cancelar", "não confirmo", "nao confirmo"}


def _valid_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=LOCAL_TZ)
        local = parsed.astimezone(LOCAL_TZ)
    except (TypeError, ValueError):
        return None
    now = datetime.now(LOCAL_TZ)
    if not now < local <= now + timedelta(days=180):
        return None
    if local.weekday() >= 5 or not 8 <= local.hour < 20:
        return None
    return local


def build_graph(*, model, session_factory, checkpointer):
    def router(state: ConversationState, config):
        text = _last_human(state)
        if is_emergency(text):
            intent = "triage"
        elif state.get("phase") in ("collecting", "awaiting_confirmation", "booked") and (
            _affirmative(text) or _negative(text)
        ):
            intent = "scheduling"
        else:
            intent = model.classify(state["messages"], config=config)
        if intent not in ("scheduling", "information", "triage"):
            intent = "information"
        update = {"next_node": intent, "intent": intent}
        if intent != "scheduling" and state.get("phase") == "awaiting_confirmation":
            update.update(phase="collecting", confirmation_key=None)
        return update

    def triage(state: ConversationState, config):
        text = _last_human(state)
        reply = EMERGENCY_REPLY if is_emergency(text) else model.triage(state["messages"], config=config)
        return {"messages": [AIMessage(content=reply)], "current_agent": "triage"}

    def information(state: ConversationState, config):
        reply = model.information(state["messages"], session_factory, config=config)
        return {"messages": [AIMessage(content=reply)], "current_agent": "information"}

    def scheduling(state: ConversationState, config):
        text = _last_human(state)
        draft = dict(state.get("draft") or {})
        phase = state.get("phase")
        previous_id = state.get("appointment_id")
        if phase == "booked" and _affirmative(text) and previous_id:
            return {"messages": [AIMessage(content=f"Sua consulta já está confirmada. Número do agendamento: {previous_id}.")],
                    "current_agent": "scheduling"}
        if phase == "booked":
            draft = {}
            previous_id = None
        if phase == "awaiting_confirmation" and _negative(text):
            return {"messages": [AIMessage(content="Tudo bem. Qual dado ou horário você deseja alterar?")],
                    "phase": "collecting", "confirmation_key": None, "current_agent": "scheduling"}
        if phase == "awaiting_confirmation" and _affirmative(text):
            result = book_appointment(
                session_factory,
                slot_id=draft["slot_id"], name=draft["name"], cpf=draft["cpf"],
                phone=draft["phone"], mode=draft["mode"], channel=state.get("channel", "unknown"),
                confirmation_key=state["confirmation_key"],
            )
            if result.status in ("booked", "already_booked"):
                return {"messages": [AIMessage(content=(
                    f"Consulta confirmada! Número do agendamento: {result.appointment_id}. "
                    f"{draft['specialty']} em {draft['slot_datetime']} ({draft['mode']})."
                ))], "appointment_id": result.appointment_id, "phase": "booked", "current_agent": "scheduling"}
            return {"messages": [AIMessage(content="Esse horário não está mais disponível. Escolha outro horário cadastrado.")],
                    "phase": "collecting", "draft": {**draft, "slot_id": None, "slot_datetime": None},
                    "confirmation_key": None, "current_agent": "scheduling"}

        extracted = model.extract(text, draft, config=config)
        changes = extracted.model_dump(exclude_none=True, exclude={"confirmation"})
        if "cpf" in changes:
            changes["cpf"] = digits(changes["cpf"])
        if "phone" in changes:
            changes["phone"] = digits(changes["phone"])
        draft.update(changes)
        if "datetime_iso" in changes or "specialty" in changes:
            draft.pop("slot_id", None)
            draft.pop("slot_datetime", None)

        if not draft.get("specialty"):
            reply = "Qual especialidade você deseja agendar?"
        elif not draft.get("datetime_iso"):
            available = list_slots(session_factory, draft["specialty"])[:3]
            options = ", ".join(item["slot_datetime"] for item in available)
            reply = (f"Qual data e horário prefere? Vagas cadastradas: {options}." if options
                     else "Não há horários cadastrados para essa especialidade no momento.")
        else:
            requested = _valid_datetime(draft["datetime_iso"])
            if requested is None:
                draft.pop("datetime_iso", None)
                reply = "Informe uma data futura, de segunda a sexta, entre 8h e 20h, com horário exato."
            else:
                desired = display_slot_datetime(requested)
                matches = [s for s in list_slots(session_factory, draft["specialty"])
                           if s["slot_datetime"] == desired]
                if not matches:
                    draft.pop("datetime_iso", None)
                    available = list_slots(session_factory, draft["specialty"])[:3]
                    options = ", ".join(s["slot_datetime"] for s in available)
                    reply = (f"Esse horário não está disponível. Vagas: {options}." if options
                             else "Não há horários cadastrados para essa especialidade no momento.")
                else:
                    draft["slot_id"] = matches[0]["id"]
                    draft["slot_datetime"] = desired
                    if not draft.get("name"):
                        reply = "Qual é o nome completo do paciente?"
                    elif not draft.get("cpf"):
                        reply = "Qual é o CPF do paciente?"
                    elif not valid_cpf(draft["cpf"]):
                        draft.pop("cpf", None)
                        reply = "O CPF informado não é válido. Pode conferir e enviar novamente?"
                    elif not draft.get("phone"):
                        reply = "Qual é o telefone com DDD para contato?"
                    elif not valid_phone(draft["phone"]):
                        draft.pop("phone", None)
                        reply = "Informe um telefone com DDD válido."
                    elif not draft.get("mode"):
                        reply = "A consulta será presencial ou por teleconsulta?"
                    else:
                        key = str(uuid4())
                        reply = (f"Posso confirmar {draft['specialty']} para {draft['name']} em "
                                 f"{desired} ({draft['mode']})? Responda 'sim' para confirmar.")
                        return {"messages": [AIMessage(content=reply)], "draft": draft,
                                "phase": "awaiting_confirmation", "confirmation_key": key,
                                "appointment_id": previous_id, "current_agent": "scheduling"}
        return {"messages": [AIMessage(content=reply)], "draft": draft,
                "phase": "collecting", "confirmation_key": None,
                "appointment_id": previous_id, "current_agent": "scheduling"}

    builder = StateGraph(ConversationState)
    builder.add_node("router", router)
    builder.add_node("triage", triage)
    builder.add_node("information", information)
    builder.add_node("scheduling", scheduling)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", lambda state: state["next_node"], {
        "triage": "triage", "information": "information", "scheduling": "scheduling",
    })
    for node in ("triage", "information", "scheduling"):
        builder.add_edge(node, END)
    return builder.compile(checkpointer=checkpointer)
