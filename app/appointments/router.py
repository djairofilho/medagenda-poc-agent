from fastapi import APIRouter, HTTPException, Query, Request

from app.appointments.schemas import AppointmentListResponse, AppointmentResponse
from app.appointments import service

router = APIRouter()


@router.get("/appointments", response_model=AppointmentListResponse)
def get_appointments(request: Request, limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0)):
    total, appointments = service.list_appointments(request.app.state.session_factory, limit, offset)
    return {"total": total, "appointments": appointments}


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_detail(appointment_id: int, request: Request):
    appointment = service.get_appointment(request.app.state.session_factory, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    return appointment
