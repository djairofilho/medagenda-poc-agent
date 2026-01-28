"""Tests for ExtractResult schema validation and normalization"""
import pytest
from app.agent.extractor.schema import ExtractResult, AppointmentMode


def test_extract_result_defaults():
    """Test default values"""
    result = ExtractResult()
    
    assert result.out_of_scope is False
    assert result.urgent_flag is False
    assert result.name is None
    assert result.phone is None
    assert result.specialty is None
    assert result.preferred_datetime is None
    assert result.mode == AppointmentMode.NAO_INFORMADO
    assert result.reason is None
    assert result.confidence == 0.5


def test_trim_strings():
    """Test string trimming"""
    result = ExtractResult(
        name="  João Silva  ",
        phone="  11987654321  ",
        specialty="  dermatologista  ",
    )
    
    assert result.name == "João Silva"
    assert result.phone == "11987654321"
    assert result.specialty == "dermatologista"


def test_clamp_confidence():
    """Test confidence clamping to [0, 1]"""
    result1 = ExtractResult(confidence=-0.5)
    assert result1.confidence == 0.0
    
    result2 = ExtractResult(confidence=1.5)
    assert result2.confidence == 1.0
    
    result3 = ExtractResult(confidence=0.7)
    assert result3.confidence == 0.7


def test_truncate_reason():
    """Test reason truncation to 100 chars"""
    long_reason = "a" * 150
    result = ExtractResult(reason=long_reason)
    
    assert len(result.reason) == 100
    assert result.reason == "a" * 100


def test_appointment_mode_enum():
    """Test AppointmentMode enum"""
    result1 = ExtractResult(mode=AppointmentMode.PRESENCIAL)
    assert result1.mode == AppointmentMode.PRESENCIAL
    assert result1.mode.value == "presencial"
    
    result2 = ExtractResult(mode="online")
    assert result2.mode == AppointmentMode.ONLINE


def test_to_dict():
    """Test conversion to dict"""
    result = ExtractResult(
        name="João Silva",
        phone="11987654321",
        specialty="dermatologista",
        preferred_datetime="amanhã",
        mode=AppointmentMode.PRESENCIAL,
        reason="check-up",
    )
    
    d = result.to_dict()
    
    assert d['name'] == "João Silva"
    assert d['phone'] == "11987654321"
    assert d['specialty'] == "dermatologista"
    assert d['preferred_datetime'] == "amanhã"
    assert d['mode'] == "presencial"
    assert d['reason'] == "check-up"


def test_count_filled_fields():
    """Test counting filled required fields"""
    result1 = ExtractResult()
    assert result1.count_filled_fields() == 0
    
    result2 = ExtractResult(
        name="João",
        phone="11987654321",
    )
    assert result2.count_filled_fields() == 2
    
    result3 = ExtractResult(
        name="João",
        phone="11987654321",
        specialty="dermatologista",
        preferred_datetime="amanhã",
    )
    assert result3.count_filled_fields() == 4


def test_empty_strings_become_none():
    """Test that empty strings are converted to None"""
    result = ExtractResult(
        name="   ",
        phone="",
    )
    
    assert result.name is None
    assert result.phone is None
