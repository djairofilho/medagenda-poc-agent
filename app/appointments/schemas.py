from pydantic import BaseModel


class AppointmentResponse(BaseModel):
    id: int
    created_at: str
    name: str
    phone: str
    specialty: str
    preferred_datetime: str
    mode: str
    reason: str | None
    status: str
    channel: str


class AppointmentListResponse(BaseModel):
    total: int
    appointments: list[AppointmentResponse]
