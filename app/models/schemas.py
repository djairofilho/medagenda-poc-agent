"""Pydantic schemas for request/response validation"""
from typing import Optional, Any, Dict, List
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
    appointments: List[AppointmentResponse]


class SessionResetResponse(BaseModel):
    """Response schema for session reset."""
    session_id: str
    message: str


# --- Availability Slots ---

class SlotBase(BaseModel):
    """Base schema for a slot."""
    specialty: str
    slot_datetime: str


class SlotCreateRequest(BaseModel):
    """Request schema for bulk slot creation."""
    slots: List[SlotBase]


class SlotResponse(SlotBase):
    """Response schema for a slot."""
    id: int
    is_available: bool
    created_at: str


class SlotListResponse(BaseModel):
    """Response schema for list of slots."""
    total: int
    slots: List[SlotResponse]


# --- Bulk Actions ---

class BulkDeleteRequest(BaseModel):
    """Request schema for bulk deletion of items by ID."""
    ids: List[int]


class BulkActionResponse(BaseModel):
    """Response schema for bulk operations."""
    affected_count: int
    message: str
