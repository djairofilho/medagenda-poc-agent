"""Extractor module - PydanticAI-based structured extraction"""
from .adapter import extract_with_pydantic_ai
from .schema import ExtractResult, AppointmentMode

__all__ = ['extract_with_pydantic_ai', 'ExtractResult', 'AppointmentMode']
