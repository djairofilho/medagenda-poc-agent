"""FastAPI application for medAgenda appointment scheduling agent"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import API_TITLE, API_VERSION, API_DESCRIPTION, DEBUG
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    AppointmentResponse,
    AppointmentListResponse,
    SessionResetResponse
)
from app.agent.graph import process_message, reset_session, get_or_create_session
from app.db.sqlite import (
    init_db,
    get_appointment,
    list_appointments,
    count_appointments
)


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
            "reset_session": "POST /sessions/{session_id}/reset"
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
                "awaiting_confirmation": state['awaiting_confirmation'],
                "appointment_id": state['appointment_id'],
                "intent": state['intent']
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
