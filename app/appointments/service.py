"""Booking transaction and read models."""

from dataclasses import dataclass
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from app.availability.service import display_slot_datetime
from app.infrastructure.models import Appointment, AvailabilitySlot, Patient
from app.patients.service import digits, valid_cpf, valid_phone


@dataclass(frozen=True)
class BookingResult:
    status: str
    appointment_id: int | None = None


def serialize_appointment(appointment: Appointment) -> dict:
    return {
        "id": appointment.id,
        "created_at": appointment.created_at.isoformat(),
        "name": appointment.patient.name,
        "phone": appointment.patient.phone,
        "specialty": appointment.specialty,
        "preferred_datetime": display_slot_datetime(appointment.preferred_datetime),
        "mode": appointment.mode,
        "reason": appointment.reason,
        "status": appointment.status,
        "channel": appointment.channel,
    }


def get_appointment(session_factory, appointment_id: int) -> dict | None:
    with session_factory() as session:
        appointment = session.scalar(
            select(Appointment).options(joinedload(Appointment.patient)).where(Appointment.id == appointment_id)
        )
        return serialize_appointment(appointment) if appointment else None


def list_appointments(session_factory, limit: int, offset: int) -> tuple[int, list[dict]]:
    with session_factory() as session:
        total = session.scalar(select(func.count(Appointment.id))) or 0
        appointments = session.scalars(
            select(Appointment)
            .options(joinedload(Appointment.patient))
            .order_by(Appointment.created_at.desc(), Appointment.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return total, [serialize_appointment(item) for item in appointments]


def book_appointment(session_factory, *, slot_id: int, name: str, cpf: str, phone: str,
                     mode: str, channel: str, confirmation_key: str) -> BookingResult:
    """A conditional UPDATE arbitrates concurrent bookings in PostgreSQL."""
    if not name.strip() or not valid_cpf(cpf) or not valid_phone(phone) or mode not in ("presencial", "teleconsulta"):
        return BookingResult("invalid")
    with session_factory.begin() as session:
        existing = session.scalar(select(Appointment.id).where(Appointment.confirmation_key == confirmation_key))
        if existing:
            return BookingResult("already_booked", existing)
        slot = session.scalar(
            update(AvailabilitySlot)
            .where(AvailabilitySlot.id == slot_id, AvailabilitySlot.is_available.is_(True))
            .values(is_available=False)
            .returning(AvailabilitySlot)
        )
        if slot is None:
            # A concurrent request may have committed the same confirmation key.
            existing = session.scalar(select(Appointment.id).where(Appointment.confirmation_key == confirmation_key))
            return BookingResult("already_booked", existing) if existing else BookingResult("unavailable")
        patient_id = session.scalar(
            insert(Patient)
            .values(name=name.strip(), cpf=digits(cpf), phone=digits(phone), channel=channel)
            .on_conflict_do_update(
                index_elements=[Patient.cpf],
                set_={"name": name.strip(), "phone": digits(phone), "channel": channel},
            )
            .returning(Patient.id)
        )
        appointment = Appointment(
            patient_id=patient_id,
            slot_id=slot.id,
            confirmation_key=confirmation_key,
            specialty=slot.specialty,
            preferred_datetime=slot.slot_datetime,
            mode=mode,
            reason=None,
            status="confirmed",
            channel=channel,
        )
        session.add(appointment)
        session.flush()
        return BookingResult("booked", appointment.id)
