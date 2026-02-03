"""FastAPI application for medAgenda appointment scheduling agent"""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, DEBUG
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AppointmentResponse,
    AppointmentListResponse,
    SessionResetResponse,
    SlotCreateRequest,
    SlotListResponse,
    SlotResponse,
    BulkDeleteRequest,
    BulkActionResponse
)
from app.agent.graph import process_message, reset_session, get_or_create_session
from app.db.sqlite import (
    init_db,
    get_appointment,
    list_appointments,
    count_appointments,
    list_available_slots,
    insert_slots_bulk,
    delete_slots_bulk
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For POC - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "medAgenda API - Appointment Scheduling Agent",
        "version": API_VERSION,
        "endpoints": {
            "chat": "POST /chat",
            "appointments": "GET /appointments",
            "appointment_detail": "GET /appointments/{id}",
            "reset_session": "POST /sessions/{session_id}/reset",
            "list_slots": "GET /slots",
            "create_slots": "POST /slots",
            "delete_slots": "DELETE /slots"
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    debug: int = Query(0, description="Set to 1 to include state debug info")
):
    """
    Process a chat message through the appointment scheduling agent.
    
    Args:
        request: Chat request with session_id, message, and optional channel
        debug: If 1, include debug state information in response
    
    Returns:
        Bot's reply and optional debug state
    """
    try:
        # Process message through agent
        reply = process_message(
            session_id=request.session_id,
            user_message=request.message,
            channel=request.channel
        )
        
        response = ChatResponse(
            session_id=request.session_id,
            reply=reply
        )
        
        # Add debug info if requested
        if debug == 1 and DEBUG:
            state = get_or_create_session(request.session_id, request.channel)
            response.state_debug = {
                "extracted": state['extracted'],
                "missing_fields": state['missing_fields'],
                "awaiting_confirmation": state.get('waiting_confirmation'),
                "appointment_id": state['appointment_id'],
                "intent": state['intent']
            }
        
        return response
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing message for session {request.session_id}: {error_msg}")
        
        # Check for specific error types
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="O serviço está temporariamente sobrecarregado. Por favor, aguarde alguns segundos e tente novamente."
            )
        elif "NOT_FOUND" in error_msg or "404" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Serviço de IA temporariamente indisponível. Por favor, tente novamente em instantes."
            )
        elif "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail="A requisição demorou muito para processar. Por favor, tente novamente."
            )
        else:
            # Generic error - don't expose internal details to user
            raise HTTPException(
                status_code=500,
                detail="Ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
            )


@app.get("/appointments", response_model=AppointmentListResponse)
async def get_appointments(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of appointments to return"),
    offset: int = Query(0, ge=0, description="Number of appointments to skip")
):
    """
    List appointments with pagination.
    
    Args:
        limit: Maximum number of appointments (1-100)
        offset: Number of appointments to skip
    
    Returns:
        List of appointments and total count
    """
    try:
        appointments = list_appointments(limit=limit, offset=offset)
        total = count_appointments()
        
        return AppointmentListResponse(
            total=total,
            appointments=[AppointmentResponse(**apt) for apt in appointments]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointments: {str(e)}")


@app.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_detail(appointment_id: int):
    """
    Get a single appointment by ID.
    
    Args:
        appointment_id: The appointment ID
    
    Returns:
        Appointment details
    """
    try:
        appointment = get_appointment(appointment_id)
        
        if not appointment:
            raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
        
        return AppointmentResponse(**appointment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointment: {str(e)}")


@app.post("/sessions/{session_id}/reset", response_model=SessionResetResponse)
async def reset_user_session(session_id: str):
    """
    Reset/clear a session.
    
    Args:
        session_id: The session identifier to reset
    
    Returns:
        Confirmation message
    """
    try:
        reset_session(session_id)
        
        return SessionResetResponse(
            session_id=session_id,
            message="Session reset successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")


# --- Availability Slot Routes ---

@app.get("/slots", response_model=SlotListResponse)
async def get_slots(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)")
):
    """
    List available slots with optional filtering.
    """
    try:
        slots = list_available_slots(specialty=specialty, date=date)
        return SlotListResponse(
            total=len(slots),
            slots=[SlotResponse(**slot) for slot in slots]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching slots: {str(e)}")


@app.post("/slots", response_model=BulkActionResponse)
async def create_slots(request: SlotCreateRequest):
    """
    Bulk create available slots.
    """
    try:
        slots_to_insert = [slot.dict() for slot in request.slots]
        count = insert_slots_bulk(slots_to_insert)
        return BulkActionResponse(
            affected_count=count,
            message=f"{count} slots created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating slots: {str(e)}")


@app.delete("/slots", response_model=BulkActionResponse)
async def delete_slots(request: BulkDeleteRequest):
    """
    Bulk delete availability slots by ID.
    """
    try:
        count = delete_slots_bulk(request.ids)
        return BulkActionResponse(
            affected_count=count,
            message=f"{count} slots deleted successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting slots: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
