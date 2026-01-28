"""Merge LLM extraction with regex fallback"""
from typing import Dict

from app.agent.extractor.schema import ExtractResult, AppointmentMode


def merge_extractions(llm_result: ExtractResult, regex_result: Dict) -> ExtractResult:
    """
    Merge LLM extraction with regex extraction.
    
    Precedence rules:
    - Regex WINS for: phone, mode (more reliable)
    - LLM WINS for: name, specialty, preferred_datetime, reason (better at understanding)
    - Flags ALWAYS from LLM: out_of_scope, urgent_flag
    - Fill empty LLM fields with regex results
    
    Args:
        llm_result: Result from PydanticAI extraction
        regex_result: Result from regex extraction (dict)
    
    Returns:
        Merged ExtractResult
    """
    # Start with LLM result
    merged = llm_result.model_copy()
    
    # If LLM failed (confidence=0), use mostly regex
    if llm_result.confidence == 0.0:
        merged.name = regex_result.get('name')
        merged.phone = regex_result.get('phone')
        merged.specialty = regex_result.get('specialty')
        merged.preferred_datetime = regex_result.get('preferred_datetime')
        merged.reason = regex_result.get('reason')
        
        # Mode from regex
        mode_str = regex_result.get('mode')
        if mode_str:
            try:
                merged.mode = AppointmentMode(mode_str)
            except ValueError:
                merged.mode = AppointmentMode.NAO_INFORMADO
        
        # Recalculate confidence based on filled fields
        merged.confidence = _calculate_confidence(merged)
        
        print("[Merge] LLM failed, using regex extraction")
        return merged
    
    # LLM succeeded, merge strategically
    
    # 1. Regex WINS for phone (more reliable pattern matching)
    regex_phone = regex_result.get('phone')
    if regex_phone:
        merged.phone = regex_phone
        print(f"[Merge] Using regex phone: {regex_phone}")
    
    # 2. Regex WINS for mode (keyword matching is reliable)
    regex_mode = regex_result.get('mode')
    if regex_mode:
        try:
            merged.mode = AppointmentMode(regex_mode)
            print(f"[Merge] Using regex mode: {regex_mode}")
        except ValueError:
            pass  # Keep LLM mode
    
    # 3. Fill empty LLM fields with regex (if available)
    if not merged.name and regex_result.get('name'):
        merged.name = regex_result['name']
        print(f"[Merge] Filled name from regex: {merged.name}")
    
    if not merged.specialty and regex_result.get('specialty'):
        merged.specialty = regex_result['specialty']
        print(f"[Merge] Filled specialty from regex: {merged.specialty}")
    
    if not merged.preferred_datetime and regex_result.get('preferred_datetime'):
        merged.preferred_datetime = regex_result['preferred_datetime']
        print(f"[Merge] Filled datetime from regex: {merged.preferred_datetime}")
    
    if not merged.reason and regex_result.get('reason'):
        merged.reason = regex_result['reason']
        print(f"[Merge] Filled reason from regex: {merged.reason}")
    
    # 4. Adjust confidence based on merge
    filled_count = merged.count_filled_fields()
    if filled_count > llm_result.count_filled_fields():
        # Regex helped fill fields, boost confidence slightly
        merged.confidence = min(1.0, merged.confidence + 0.1)
        print(f"[Merge] Boosted confidence to {merged.confidence:.2f}")
    
    return merged


def _calculate_confidence(result: ExtractResult) -> float:
    """
    Calculate confidence based on filled fields.
    
    Used when LLM fails and we rely on regex.
    
    Args:
        result: ExtractResult to calculate confidence for
    
    Returns:
        Confidence score (0.0 to 1.0)
    """
    required_fields = 4  # name, phone, specialty, preferred_datetime
    filled = result.count_filled_fields()
    
    if filled == 0:
        return 0.0
    
    # Base confidence from filled ratio
    base = (filled / required_fields) * 0.8
    
    # Bonus for having phone (most reliable)
    if result.phone:
        base += 0.1
    
    # Clamp to [0, 1]
    return max(0.0, min(1.0, base))
