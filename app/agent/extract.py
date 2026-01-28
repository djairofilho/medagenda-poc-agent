"""Field extraction logic without LLM - using regex and heuristics"""
import re
from typing import Dict, Optional, List


# Regex patterns
PHONE_PATTERN = re.compile(
    r'(?:\+?55\s?)?'  # Optional +55 country code
    r'(?:\(?\d{2}\)?[\s-]?)?'  # Optional DDD with optional parentheses
    r'(?:9\s?)?'  # Optional 9 for mobile
    r'\d{4}[\s-]?\d{4}'  # 4 digits, optional separator, 4 digits
)

# Keywords for mode detection
MODE_KEYWORDS = {
    'presencial': ['presencial', 'pessoalmente', 'consultório', 'consultorio', 'ir até', 'ir ate'],
    'online': ['online', 'telemedicina', 'virtual', 'remoto', 'remota', 'video', 'vídeo', 'videochamada']
}

# Specialty mappings (normalize variations)
SPECIALTY_MAP = {
    'dermato': 'dermatologista',
    'dermatologista': 'dermatologista',
    'dermatologia': 'dermatologista',
    'cardio': 'cardiologista',
    'cardiologista': 'cardiologista',
    'cardiologia': 'cardiologista',
    'ortopedista': 'ortopedista',
    'ortopedia': 'ortopedista',
    'ortoped': 'ortopedista',
    'pediatra': 'pediatra',
    'pediatria': 'pediatra',
    'gineco': 'ginecologista',
    'ginecologista': 'ginecologista',
    'ginecologia': 'ginecologista',
    'oftalmo': 'oftalmologista',
    'oftalmologista': 'oftalmologista',
    'oftalmologia': 'oftalmologista',
    'neuro': 'neurologista',
    'neurologista': 'neurologista',
    'neurologia': 'neurologista',
    'psiquiatra': 'psiquiatra',
    'psiquiatria': 'psiquiatra',
    'clinico geral': 'clínico geral',
    'clínico geral': 'clínico geral',
    'clinico': 'clínico geral',
    'geral': 'clínico geral',
}

# Out-of-scope keywords (medical advice)
OUT_OF_SCOPE_KEYWORDS = [
    'diagnóstico', 'diagnostico', 'o que eu tenho', 'o que tenho',
    'tratamento', 'remédio', 'remedio', 'medicamento', 'tomar',
    'é grave', 'e grave', 'preocupar', 'normal',
    'pode ser', 'será que', 'sera que', 'devo me preocupar'
]

# Urgent keywords (require neutral response)
URGENT_KEYWORDS = [
    'dor no peito', 'falta de ar', 'desmaio', 'desmaiando',
    'sangramento', 'hemorragia', 'convulsão', 'convulsao',
    'febre alta', 'vomitando sangue', 'não consigo respirar',
    'nao consigo respirar'
]


def extract_phone(text: str) -> Optional[str]:
    """
    Extract Brazilian phone number from text.
    
    Args:
        text: Input text
    
    Returns:
        Extracted phone number or None
    """
    match = PHONE_PATTERN.search(text)
    if match:
        # Clean up the phone number
        phone = match.group(0)
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', phone)
        return phone
    return None


def extract_mode(text: str) -> Optional[str]:
    """
    Extract appointment mode (presencial/online) from text.
    
    Args:
        text: Input text
    
    Returns:
        'presencial', 'online', or None
    """
    text_lower = text.lower()
    
    for mode, keywords in MODE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return mode
    
    return None


def extract_specialty(text: str) -> Optional[str]:
    """
    Extract and normalize medical specialty from text.
    
    Args:
        text: Input text
    
    Returns:
        Normalized specialty name or None
    """
    text_lower = text.lower()
    
    # Try to match any specialty keyword
    for key, normalized in SPECIALTY_MAP.items():
        if key in text_lower:
            return normalized
    
    return None


def extract_name(text: str) -> Optional[str]:
    """
    Extract patient name from text using heuristics.
    
    Args:
        text: Input text
    
    Returns:
        Extracted name or None
    """
    text = text.strip()
    
    # Blacklist of common words that are not names
    blacklist_words = {
        'quero', 'marcar', 'consulta', 'preciso', 'gostaria', 'pode', 'ser',
        'online', 'presencial', 'amanhã', 'hoje', 'segunda', 'terça', 'quarta',
        'quinta', 'sexta', 'sábado', 'domingo', 'manhã', 'tarde', 'noite'
    }
    
    # Pattern 1: "me chamo [name]" or "sou o/a [name]" (case insensitive)
    patterns = [
        r'me chamo\s+([A-ZÀ-Úa-zà-ú]+(?:\s+[A-ZÀ-Úa-zà-ú]+)+)',
        r'sou (?:o|a)\s+([A-ZÀ-Úa-zà-ú]+(?:\s+[A-ZÀ-Úa-zà-ú]+)+)',
        r'nome[:\s]+([A-ZÀ-Úa-zà-ú]+(?:\s+[A-ZÀ-Úa-zà-ú]+)+)',
        r'meu nome é\s+([A-ZÀ-Úa-zà-ú]+(?:\s+[A-ZÀ-Úa-zà-ú]+)+)',
        r'(?:^|\s)([A-ZÀ-Ú][a-zà-ú]+\s+[A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)?)',  # Capitalized names
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Capitalize properly
            name = ' '.join(word.capitalize() for word in name.split())
            
            # Check if any word is in blacklist
            words_lower = [w.lower() for w in name.split()]
            if any(word in blacklist_words for word in words_lower):
                continue  # Skip this match
            
            # Validate: must have at least 2 words and reasonable length
            if len(name.split()) >= 2 and 3 <= len(name) <= 50:
                return name
    
    return None


def extract_datetime(text: str) -> Optional[str]:
    """
    Extract preferred date/time from text (simple capture, no normalization).
    
    Args:
        text: Input text
    
    Returns:
        Date/time text or None
    """
    text_lower = text.lower()
    
    # Look for common date/time patterns
    datetime_patterns = [
        # Complete date + time
        r'(amanhã\s+(?:às?|as?|a)?\s*\d{1,2}(?:h|:)\d{0,2})',
        r'(hoje\s+(?:às?|as?|a)?\s*\d{1,2}(?:h|:)\d{0,2})',
        r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?\s+(?:às?|as?|a)?\s*\d{1,2}(?:h|:)\d{0,2})',
        r'((?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?\s+(?:às?|as?|a)?\s*\d{1,2}(?:h|:)\d{0,2})',
        r'((?:próxima|proxima)\s+(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?)',
        r'(\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)(?:\s+(?:às?|as?|a)?\s*\d{1,2}(?:h|:)\d{0,2})?)',
        # Just weekdays
        r'((?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)(?:-feira)?)',
        # Just dates
        r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
        r'(amanhã|hoje)',
        # Just times
        r'(\d{1,2}(?:h|:)\d{0,2})',
    ]
    
    for pattern in datetime_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result = match.group(1).strip()
            # Filter out phone numbers (avoid matching times that are actually phones)
            if not re.match(r'^\d{4,}$', result.replace(':', '').replace('h', '')):
                return result
    
    return None


def extract_reason(text: str) -> Optional[str]:
    """
    Extract reason for appointment from text.
    
    Args:
        text: Input text
    
    Returns:
        Reason text or None
    """
    text_lower = text.lower()
    
    # Look for reason patterns
    reason_patterns = [
        r'(?:consulta|atendimento)\s+para\s+(.{5,50})',
        r'(?:motivo|razão|razao)[:\s]+(.{5,50})',
        r'(?:preciso|quero)\s+(?:consulta|atendimento)\s+(?:para|pra|por causa de)\s+(.{5,50})',
    ]
    
    for pattern in reason_patterns:
        match = re.search(pattern, text_lower)
        if match:
            reason = match.group(1).strip()
            # Clean up - stop at punctuation
            reason = re.split(r'[.!?]', reason)[0]
            return reason[:100]  # Limit length
    
    return None


def detect_intent(text: str) -> str:
    """
    Detect user intent to identify out-of-scope requests.
    
    Args:
        text: Input text
    
    Returns:
        'schedule' (normal), 'out_of_scope' (medical advice), or 'urgent' (emergency)
    """
    text_lower = text.lower()
    
    # Check for urgent keywords first
    for keyword in URGENT_KEYWORDS:
        if keyword in text_lower:
            return 'urgent'
    
    # Check for out-of-scope medical advice requests
    for keyword in OUT_OF_SCOPE_KEYWORDS:
        if keyword in text_lower:
            return 'out_of_scope'
    
    return 'schedule'


def extract_all_fields(text: str, current_extracted: Dict) -> Dict:
    """
    Extract all possible fields from text and merge with current extracted data.
    
    Args:
        text: User message
        current_extracted: Currently extracted fields
    
    Returns:
        Updated extracted fields dictionary
    """
    extracted = current_extracted.copy()
    
    # Extract each field if not already present
    if not extracted.get('phone'):
        phone = extract_phone(text)
        if phone:
            extracted['phone'] = phone
    
    if not extracted.get('mode'):
        mode = extract_mode(text)
        if mode:
            extracted['mode'] = mode
    
    if not extracted.get('specialty'):
        specialty = extract_specialty(text)
        if specialty:
            extracted['specialty'] = specialty
    
    if not extracted.get('name'):
        name = extract_name(text)
        if name:
            extracted['name'] = name
    
    if not extracted.get('preferred_datetime'):
        datetime_text = extract_datetime(text)
        if datetime_text:
            extracted['preferred_datetime'] = datetime_text
    
    if not extracted.get('reason'):
        reason = extract_reason(text)
        if reason:
            extracted['reason'] = reason
    
    return extracted


def get_missing_fields(extracted: Dict) -> List[str]:
    """
    Get list of required fields that are still missing.
    
    Args:
        extracted: Dictionary of extracted fields
    
    Returns:
        List of missing field names
    """
    required_fields = ['name', 'phone', 'specialty', 'preferred_datetime', 'mode']
    missing = []
    
    for field in required_fields:
        if not extracted.get(field):
            missing.append(field)
    
    return missing
