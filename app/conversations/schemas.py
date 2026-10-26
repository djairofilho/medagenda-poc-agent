from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str
    channel: str | None = "unknown"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    state_debug: dict[str, Any] | None = None


class SessionResetResponse(BaseModel):
    session_id: str
    message: str
