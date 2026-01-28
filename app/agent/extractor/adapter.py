"""Main adapter for PydanticAI extraction with fallback"""
from typing import Optional
import asyncio

from app.agent.extractor.schema import ExtractResult
from app.agent.extractor.factory import create_agent


def extract_with_pydantic_ai(user_text: str) -> ExtractResult:
    """
    Extract structured data from user message using PydanticAI.
    
    Falls back to empty ExtractResult (confidence=0.0) if:
    - No provider configured
    - Provider fails
    - Timeout
    - Any other error
    
    Args:
        user_text: User's message
    
    Returns:
        ExtractResult with extracted data or fallback
    """
    # Create agent
    agent = create_agent()
    
    # If no agent (fallback mode), return empty result with regex intent
    if agent is None:
        print("[Adapter] No agent configured, using fallback")
        return _create_fallback_result(user_text)
    
    try:
        # Run extraction with timeout
        result = asyncio.run(_run_extraction_with_timeout(agent, user_text, timeout=5.0))
        
        if result is None:
            print("[Adapter] Extraction timed out, using fallback")
            return _create_fallback_result(user_text)
        
        # Validate and return
        print(f"[Adapter] Extraction successful (confidence={result.confidence:.2f})")
        return result
        
    except Exception as e:
        print(f"[Adapter] Extraction failed: {e}, using fallback")
        return _create_fallback_result(user_text)


async def _run_extraction_with_timeout(agent, user_text: str, timeout: float) -> Optional[ExtractResult]:
    """
    Run extraction with timeout.
    
    Args:
        agent: PydanticAI agent
        user_text: User message
        timeout: Timeout in seconds
    
    Returns:
        ExtractResult or None if timeout
    """
    try:
        result = await asyncio.wait_for(
            agent.run(user_text),
            timeout=timeout
        )
        return result.data
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        print(f"[Adapter] Extraction error: {e}")
        return None


def _create_fallback_result(user_text: str = "") -> ExtractResult:
    """
    Create fallback ExtractResult with confidence=0.0.
    
    Uses regex-based intent detection as backup when LLM is not available.
    
    Args:
        user_text: User message for intent detection
    
    Returns:
        Empty ExtractResult with confidence=0.0 and intent flags from regex
    """
    # Use regex intent detection as fallback
    from app.agent.extract import detect_intent
    
    intent = detect_intent(user_text) if user_text else 'schedule'
    
    return ExtractResult(
        out_of_scope=(intent == 'out_of_scope'),
        urgent_flag=(intent == 'urgent'),
        name=None,
        phone=None,
        specialty=None,
        preferred_datetime=None,
        mode="nao_informado",
        reason=None,
        confidence=0.0,  # Indicates fallback
    )
