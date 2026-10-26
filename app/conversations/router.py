"""Chat and session HTTP contracts used by Streamlit."""

import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app import config
from app.conversations.schemas import ChatRequest, ChatResponse, SessionResetResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, debug: int = Query(0)):
    service = request.app.state.conversations
    try:
        reply = service.process_message(payload.session_id, payload.message, payload.channel or "unknown")
    except Exception as exc:
        logger.error("Chat failed for session %s (%s)", payload.session_id, type(exc).__name__)
        message = str(exc)
        if "RESOURCE_EXHAUSTED" in message or "429" in message:
            raise HTTPException(429, "O serviço está temporariamente sobrecarregado. Tente novamente.") from exc
        if "timeout" in message.lower():
            raise HTTPException(504, "A requisição demorou muito para processar. Tente novamente.") from exc
        if isinstance(exc, RuntimeError) and "Configure LLM_PROVIDER" in message:
            raise HTTPException(503, "Serviço de IA não configurado.") from exc
        raise HTTPException(500, "Ocorreu um erro ao processar sua mensagem.") from exc
    response = ChatResponse(session_id=payload.session_id, reply=reply)
    if debug == 1 and config.DEBUG:
        state = service.state(payload.session_id)
        draft = state.get("draft") or {}
        response.state_debug = {
            "extracted": {key: draft.get(key) for key in ("specialty", "slot_datetime", "mode") if draft.get(key)},
            "missing_fields": [],
            "awaiting_confirmation": state.get("phase") == "awaiting_confirmation",
            "appointment_id": state.get("appointment_id"),
            "intent": state.get("intent"),
        }
    return response


@router.post("/sessions/{session_id}/reset", response_model=SessionResetResponse)
def reset_session(session_id: str, request: Request):
    request.app.state.conversations.reset(session_id)
    return SessionResetResponse(session_id=session_id, message="Session reset successfully")
