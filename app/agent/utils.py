import re
from datetime import datetime

def format_date_br(date_obj: datetime) -> str:
    """Format datetime to Brazilian string format dd/mm/yyyy HH:MM."""
    if not date_obj:
        return ""
    return date_obj.strftime("%d/%m/%Y %H:%M")

def validate_cpf(cpf: str) -> bool:
    """
    Simple checks for CPF format. 
    Does not implement full digit verification algorithm for this POC.
    """
    clean_cpf = re.sub(r'\D', '', str(cpf))
    return len(clean_cpf) == 11

def validate_phone(phone: str) -> bool:
    """
    Simple check for phone format (mobile).
    Expected at least 10-11 digits.
    """
    clean_phone = re.sub(r'\D', '', str(phone))
    return 10 <= len(clean_phone) <= 13


def validate_datetime_string(datetime_str: str) -> tuple[bool, str, datetime | None]:
    """
    Valida string de data/hora e retorna resultado.
    
    Args:
        datetime_str: String contendo data/hora
    
    Returns:
        Tupla (is_valid, message, datetime_obj)
    """
    from app.agent.datetime_parser import extract_datetime_info
    
    result = extract_datetime_info(datetime_str)
    
    return (
        result["is_valid"],
        result["validation_message"],
        result["datetime_obj"]
    )


def parse_user_datetime(user_input: str) -> dict:
    """
    Parse entrada do usuário e retorna informações completas de data/hora.
    
    Args:
        user_input: Texto do usuário
    
    Returns:
        Dict com datetime_obj, formatted, is_valid, confidence, etc.
    """
    from app.agent.datetime_parser import extract_datetime_info
    return extract_datetime_info(user_input)


from app.config import LLM_PROVIDER, GOOGLE_API_KEY, OPENAI_API_KEY, GEMINI_MODEL, OPENAI_MODEL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

def get_llm():
    """Factory to get the configured LLM."""
    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY, max_retries=2)
    elif LLM_PROVIDER == "gemini" or GOOGLE_API_KEY:
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, max_retries=2)
    else:
        # Fallback or error
        print("Warning: No valid LLM provider found. Using fallback mock.")
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="todo")
