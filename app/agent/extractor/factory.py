"""Factory for creating PydanticAI agents with different providers"""
import os
from typing import Optional
from pydantic_ai import Agent

from app.agent.extractor.schema import ExtractResult
from app.agent.extractor.prompts import SYSTEM_INSTRUCTIONS
from app.config import (
    LLM_PROVIDER,
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
)


def get_provider_from_env() -> str:
    """
    Get LLM provider from environment.
    
    Returns:
        Provider name: 'gemini', 'openai', 'anthropic', or 'fallback'
    """
    return LLM_PROVIDER.lower()


def create_gemini_agent() -> Optional[Agent[None, ExtractResult]]:
    """
    Create PydanticAI agent with Gemini provider.
    
    Returns:
        Agent instance or None if configuration is missing
    """
    if not GOOGLE_API_KEY:
        return None
    
    try:
        from pydantic_ai.models.gemini import GeminiModel
        
        model = GeminiModel(
            model_name=GEMINI_MODEL,
            api_key=GOOGLE_API_KEY,
        )
        
        agent = Agent(
            model=model,
            result_type=ExtractResult,
            system_prompt=SYSTEM_INSTRUCTIONS,
            retries=2,
        )
        
        return agent
    except Exception as e:
        print(f"[Factory] Failed to create Gemini agent: {e}")
        return None


def create_openai_agent() -> Optional[Agent[None, ExtractResult]]:
    """
    Create PydanticAI agent with OpenAI provider.
    
    Returns:
        Agent instance or None if configuration is missing
    """
    if not OPENAI_API_KEY:
        return None
    
    try:
        from pydantic_ai.models.openai import OpenAIModel
        
        model = OpenAIModel(
            model_name=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
        )
        
        agent = Agent(
            model=model,
            result_type=ExtractResult,
            system_prompt=SYSTEM_INSTRUCTIONS,
            retries=2,
        )
        
        return agent
    except Exception as e:
        print(f"[Factory] Failed to create OpenAI agent: {e}")
        return None


def create_anthropic_agent() -> Optional[Agent[None, ExtractResult]]:
    """
    Create PydanticAI agent with Anthropic provider.
    
    Returns:
        Agent instance or None if configuration is missing
    """
    if not ANTHROPIC_API_KEY:
        return None
    
    try:
        from pydantic_ai.models.anthropic import AnthropicModel
        
        model = AnthropicModel(
            model_name=ANTHROPIC_MODEL,
            api_key=ANTHROPIC_API_KEY,
        )
        
        agent = Agent(
            model=model,
            result_type=ExtractResult,
            system_prompt=SYSTEM_INSTRUCTIONS,
            retries=2,
        )
        
        return agent
    except Exception as e:
        print(f"[Factory] Failed to create Anthropic agent: {e}")
        return None


def create_agent(provider: Optional[str] = None) -> Optional[Agent[None, ExtractResult]]:
    """
    Create PydanticAI agent based on provider.
    
    Args:
        provider: Provider name ('gemini', 'openai', 'anthropic', 'fallback')
                 If None, reads from environment
    
    Returns:
        Agent instance or None for fallback
    """
    if provider is None:
        provider = get_provider_from_env()
    
    provider = provider.lower()
    
    if provider == 'gemini':
        return create_gemini_agent()
    elif provider == 'openai':
        return create_openai_agent()
    elif provider == 'anthropic':
        return create_anthropic_agent()
    elif provider == 'fallback':
        return None
    else:
        print(f"[Factory] Unknown provider '{provider}', using fallback")
        return None
