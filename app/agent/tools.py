"""Utility tools for the agent"""
from typing import Dict, Any


def is_affirmative(text: str) -> bool:
    """
    Check if text is an affirmative response.
    
    Args:
        text: User input
    
    Returns:
        True if affirmative, False otherwise
    """
    text_lower = text.lower().strip()
    affirmative_words = ['sim', 's', 'yes', 'confirmar', 'confirmo', 'ok', 'okay', 'certo']
    
    return text_lower in affirmative_words


def is_negative(text: str) -> bool:
    """
    Check if text is a negative response.
    
    Args:
        text: User input
    
    Returns:
        True if negative, False otherwise
    """
    text_lower = text.lower().strip()
    negative_words = ['não', 'nao', 'n', 'no', 'nope', 'negativo']
    
    return text_lower in negative_words


def create_message(role: str, content: str) -> Dict[str, str]:
    """
    Create a message dictionary.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
    
    Returns:
        Message dictionary
    """
    return {"role": role, "content": content}


def get_last_user_message(messages: list) -> str:
    """
    Get the last user message from messages list.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        Last user message content or empty string
    """
    for message in reversed(messages):
        if message.get('role') == 'user':
            return message.get('content', '')
    return ''
