"""Pydantic schema for structured extraction - Source of Truth"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AppointmentMode(str, Enum):
    """Appointment mode enum"""
    PRESENCIAL = "presencial"
    ONLINE = "online"
    NAO_INFORMADO = "nao_informado"


class ExtractResult(BaseModel):
    """
    Structured extraction result from user message.
    
    This is the single source of truth for all extracted data.
    """
    # Flags
    out_of_scope: bool = Field(
        default=False,
        description="True if user is asking for diagnosis/treatment/medical advice"
    )
    urgent_flag: bool = Field(
        default=False,
        description="True if user mentions urgent symptoms (chest pain, difficulty breathing, etc.)"
    )
    
    # Patient data
    name: Optional[str] = Field(
        default=None,
        description="Patient's full name"
    )
    phone: Optional[str] = Field(
        default=None,
        description="Patient's phone number (digits only)"
    )
    specialty: Optional[str] = Field(
        default=None,
        description="Medical specialty (normalized: dermatologista, cardiologista, etc.)"
    )
    preferred_datetime: Optional[str] = Field(
        default=None,
        description="Preferred date/time as free text (e.g., 'amanhã às 14h', '15/02')"
    )
    mode: AppointmentMode = Field(
        default=AppointmentMode.NAO_INFORMADO,
        description="Appointment mode: presencial, online, or nao_informado"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Brief reason for appointment (administrative only, max 100 chars)"
    )
    
    # Metadata
    confidence: float = Field(
        default=0.5,
        description="Confidence score (0.0 to 1.0)"
    )
    
    @field_validator('name', 'phone', 'specialty', 'preferred_datetime', 'reason', mode='before')
    @classmethod
    def trim_strings(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from string fields"""
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None
    
    @field_validator('confidence', mode='before')
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0.0 and 1.0"""
        return max(0.0, min(1.0, v))
    
    @field_validator('reason', mode='before')
    @classmethod
    def truncate_reason(cls, v: Optional[str]) -> Optional[str]:
        """Ensure reason doesn't exceed 100 characters"""
        if v is None:
            return None
        return v[:100] if len(v) > 100 else v
    
    def to_dict(self) -> dict:
        """Convert to dictionary for compatibility with existing code"""
        return {
            'name': self.name,
            'phone': self.phone,
            'specialty': self.specialty,
            'preferred_datetime': self.preferred_datetime,
            'mode': self.mode.value,
            'reason': self.reason,
        }
    
    def count_filled_fields(self) -> int:
        """Count how many required fields are filled"""
        required = ['name', 'phone', 'specialty', 'preferred_datetime']
        return sum(1 for field in required if getattr(self, field) is not None)
