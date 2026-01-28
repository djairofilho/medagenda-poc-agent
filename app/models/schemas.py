"""Pydantic schemas for request/response validation"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message")
    channel: Optional[str] = Field(default="unknown", description="Communication channel (web|whatsapp|instagram|unknown)")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    session_id: str = Field(..., description="Session identifier")
    reply: str = Field(..., description="Bot's reply message")
    state_debug: Optional[Dict[str, Any]] = Field(default=None, description="Debug state information (only if debug=1)")


class AppointmentResponse(BaseModel):
    """Response schema for appointment data."""
    id: int
    created_at: str
    name: str
    phone: str
    specialty: str
    preferred_datetime: str
    mode: str
    reason: Optional[str]
    status: str
    channel: str


class AppointmentListResponse(BaseModel):
    """Response schema for list of appointments."""
    total: int
    appointments: list[AppointmentResponse]


class SessionResetResponse(BaseModel):
    """Response schema for session reset."""
    session_id: str
    message: str
