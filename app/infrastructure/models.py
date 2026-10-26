"""Relational mappings. HTTP and agent state do not depend on these classes."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    name: Mapped[str] = mapped_column(String(200))
    cpf: Mapped[str] = mapped_column(String(11), unique=True)
    phone: Mapped[str] = mapped_column(String(20))
    channel: Mapped[str] = mapped_column(String(30), default="unknown")


class AvailabilitySlot(Base):
    __tablename__ = "availability"
    __table_args__ = (UniqueConstraint("specialty", "slot_datetime", name="uq_availability_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    specialty: Mapped[str] = mapped_column(String(120), index=True)
    slot_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("availability.id", ondelete="RESTRICT"), unique=True)
    confirmation_key: Mapped[str] = mapped_column(String(100), unique=True)
    specialty: Mapped[str] = mapped_column(String(120))
    preferred_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mode: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    channel: Mapped[str] = mapped_column(String(30), default="unknown")

    patient: Mapped[Patient] = relationship()
    slot: Mapped[AvailabilitySlot] = relationship()


class ClinicInfo(Base):
    __tablename__ = "clinic_info"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
