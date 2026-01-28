"""Tests for merge logic between LLM and regex extractions"""
import pytest
from app.agent.extractor.schema import ExtractResult, AppointmentMode
from app.agent.extractor.merge import merge_extractions


def test_merge_llm_failed_uses_regex():
    """When LLM fails (confidence=0), should use regex results"""
    llm_result = ExtractResult(confidence=0.0)
    
    regex_result = {
        'name': 'João Silva',
        'phone': '11987654321',
        'specialty': 'dermatologista',
        'preferred_datetime': 'amanhã',
        'mode': 'presencial',
        'reason': 'check-up',
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    assert merged.name == 'João Silva'
    assert merged.phone == '11987654321'
    assert merged.specialty == 'dermatologista'
    assert merged.preferred_datetime == 'amanhã'
    assert merged.mode == AppointmentMode.PRESENCIAL
    assert merged.reason == 'check-up'
    assert merged.confidence > 0.0  # Recalculated


def test_merge_regex_wins_phone():
    """Regex should win for phone (more reliable)"""
    llm_result = ExtractResult(
        phone='11999999999',  # LLM extracted
        confidence=0.8,
    )
    
    regex_result = {
        'phone': '11987654321',  # Regex extracted (wins)
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    assert merged.phone == '11987654321'  # Regex wins


def test_merge_regex_wins_mode():
    """Regex should win for mode (keyword matching is reliable)"""
    llm_result = ExtractResult(
        mode=AppointmentMode.NAO_INFORMADO,  # LLM didn't detect
        confidence=0.7,
    )
    
    regex_result = {
        'mode': 'presencial',  # Regex detected (wins)
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    assert merged.mode == AppointmentMode.PRESENCIAL  # Regex wins


def test_merge_llm_wins_semantic_fields():
    """LLM should win for semantic fields (name, specialty, etc.)"""
    llm_result = ExtractResult(
        name='João Silva',
        specialty='dermatologista',
        preferred_datetime='amanhã às 14h',
        confidence=0.9,
    )
    
    regex_result = {
        'name': 'João',  # Regex extracted less complete
        'specialty': 'dermato',  # Regex extracted variation
        'preferred_datetime': 'amanhã',  # Regex extracted partial
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    # LLM wins for semantic fields
    assert merged.name == 'João Silva'
    assert merged.specialty == 'dermatologista'
    assert merged.preferred_datetime == 'amanhã às 14h'


def test_merge_fills_empty_llm_fields():
    """Regex should fill empty LLM fields"""
    llm_result = ExtractResult(
        name='João Silva',
        # phone missing
        specialty='dermatologista',
        # preferred_datetime missing
        confidence=0.6,
    )
    
    regex_result = {
        'phone': '11987654321',  # Fill from regex
        'preferred_datetime': 'amanhã',  # Fill from regex
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    assert merged.name == 'João Silva'  # From LLM
    assert merged.phone == '11987654321'  # Filled from regex
    assert merged.specialty == 'dermatologista'  # From LLM
    assert merged.preferred_datetime == 'amanhã'  # Filled from regex


def test_merge_flags_always_from_llm():
    """Flags (out_of_scope, urgent_flag) always from LLM"""
    llm_result = ExtractResult(
        out_of_scope=True,
        urgent_flag=False,
        confidence=0.9,
    )
    
    regex_result = {}  # Regex doesn't set flags
    
    merged = merge_extractions(llm_result, regex_result)
    
    assert merged.out_of_scope is True
    assert merged.urgent_flag is False


def test_merge_boosts_confidence_when_regex_helps():
    """Confidence should increase when regex fills fields"""
    llm_result = ExtractResult(
        name='João Silva',
        confidence=0.5,
    )
    
    regex_result = {
        'phone': '11987654321',
        'specialty': 'dermatologista',
        'preferred_datetime': 'amanhã',
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    # Confidence should be boosted
    assert merged.confidence > llm_result.confidence


def test_merge_invalid_regex_mode_ignored():
    """Invalid mode from regex should be ignored"""
    llm_result = ExtractResult(
        mode=AppointmentMode.ONLINE,
        confidence=0.8,
    )
    
    regex_result = {
        'mode': 'invalid_mode',  # Invalid
    }
    
    merged = merge_extractions(llm_result, regex_result)
    
    # Should keep LLM mode
    assert merged.mode == AppointmentMode.ONLINE
