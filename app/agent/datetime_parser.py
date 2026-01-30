"""
Módulo de parsing e validação de data/hora para o sistema MedAgenda.
Suporta múltiplos formatos em português brasileiro.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
    import pytz
    BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
except ImportError:
    # Fallback: usar timezone offset fixo
    from datetime import timezone
    BRAZIL_TZ = timezone(timedelta(hours=-3))


# Mapeamento de dias da semana
WEEKDAYS = {
    "segunda": 0, "segunda-feira": 0, "seg": 0,
    "terça": 1, "terca": 1, "terça-feira": 1, "terca-feira": 1, "ter": 1,
    "quarta": 2, "quarta-feira": 2, "qua": 2,
    "quinta": 3, "quinta-feira": 3, "qui": 3,
    "sexta": 4, "sexta-feira": 4, "sex": 4,
    "sábado": 5, "sabado": 5, "sab": 5,
    "domingo": 6, "dom": 6
}

# Mapeamento de meses
MONTHS = {
    "janeiro": 1, "jan": 1,
    "fevereiro": 2, "fev": 2,
    "março": 3, "marco": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "maio": 5, "mai": 5,
    "junho": 6, "jun": 6,
    "julho": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "setembro": 9, "set": 9,
    "outubro": 10, "out": 10,
    "novembro": 11, "nov": 11,
    "dezembro": 12, "dez": 12
}

# Períodos do dia
TIME_PERIODS = {
    "manhã": 9, "manha": 9,
    "tarde": 14,
    "noite": 19,
    "meio-dia": 12, "meio dia": 12, "meiodia": 12,
    "meia-noite": 0, "meia noite": 0, "meianoite": 0
}


@dataclass
class ParsedDateTime:
    """Resultado do parsing de data/hora."""
    datetime_obj: Optional[datetime]
    is_valid: bool
    error_message: str = ""
    confidence: float = 1.0  # 0.0 a 1.0
    original_text: str = ""


@dataclass
class ValidationResult:
    """Resultado da validação de data/hora."""
    is_valid: bool
    message: str
    suggestions: list[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


def get_current_datetime() -> datetime:
    """Retorna a data/hora atual no timezone do Brasil."""
    return datetime.now(BRAZIL_TZ)


def parse_relative_date(text: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse datas relativas como 'amanhã', 'depois de amanhã', 'daqui a X dias'.
    """
    if reference_date is None:
        reference_date = get_current_datetime()
    
    text_lower = text.lower()
    
    # Hoje
    if re.search(r'\bhoje\b', text_lower):
        return reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Amanhã
    if re.search(r'\bamanhã\b|\bamanha\b', text_lower):
        return reference_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    # Depois de amanhã
    if re.search(r'\bdepois de amanhã\b|\bdepois de amanha\b', text_lower):
        return reference_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)
    
    # Daqui a X dias/semanas
    match = re.search(r'daqui\s+a\s+(\d+)\s+(dia|dias|semana|semanas)', text_lower)
    if match:
        quantity = int(match.group(1))
        unit = match.group(2)
        if 'semana' in unit:
            quantity *= 7
        return reference_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=quantity)
    
    return None


def parse_weekday(text: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse dias da semana como 'segunda', 'próxima terça', etc.
    """
    if reference_date is None:
        reference_date = get_current_datetime()
    
    text_lower = text.lower()
    
    # Procurar por dia da semana
    for weekday_name, weekday_num in WEEKDAYS.items():
        if weekday_name in text_lower:
            current_weekday = reference_date.weekday()
            days_ahead = weekday_num - current_weekday
            
            # Se o dia já passou esta semana, ou se tem "próxima/próximo"
            if days_ahead <= 0 or 'próxima' in text_lower or 'proximo' in text_lower or 'próximo' in text_lower:
                days_ahead += 7
            
            target_date = reference_date + timedelta(days=days_ahead)
            return target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return None


def parse_absolute_date(text: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse datas absolutas como '15/03/2026', '15/03', '15 de março'.
    """
    if reference_date is None:
        reference_date = get_current_datetime()
    
    text_lower = text.lower()
    
    # Formato DD/MM/YYYY ou DD/MM/YY
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day, tzinfo=BRAZIL_TZ)
        except ValueError:
            return None
    
    # Formato DD/MM (assume ano atual ou próximo)
    match = re.search(r'(\d{1,2})/(\d{1,2})\b', text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = reference_date.year
        try:
            result = datetime(year, month, day, tzinfo=BRAZIL_TZ)
            # Se a data já passou este ano, assume ano que vem
            if result < reference_date:
                result = datetime(year + 1, month, day, tzinfo=BRAZIL_TZ)
            return result
        except ValueError:
            return None
    
    # Formato "15 de março" ou "15 de março de 2026"
    for month_name, month_num in MONTHS.items():
        pattern = rf'(\d{{1,2}})\s+de\s+{month_name}(?:\s+de\s+(\d{{4}}))?'
        match = re.search(pattern, text_lower)
        if match:
            day = int(match.group(1))
            year = int(match.group(2)) if match.group(2) else reference_date.year
            try:
                result = datetime(year, month_num, day, tzinfo=BRAZIL_TZ)
                # Se a data já passou este ano e não especificou ano, assume ano que vem
                if result < reference_date and not match.group(2):
                    result = datetime(year + 1, month_num, day, tzinfo=BRAZIL_TZ)
                return result
            except ValueError:
                return None
    
    return None


def parse_time(text: str) -> Optional[Tuple[int, int]]:
    """
    Parse horários como '14:30', '14h30', '14h', 'manhã', 'tarde'.
    Retorna tupla (hora, minuto) ou None.
    """
    text_lower = text.lower()
    
    # Formato HH:MM
    match = re.search(r'(\d{1,2}):(\d{2})', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    
    # Formato HHhMM ou HHh
    match = re.search(r'(\d{1,2})h(\d{2})?', text_lower)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    
    # Períodos do dia
    for period_name, period_hour in TIME_PERIODS.items():
        if period_name in text_lower:
            return (period_hour, 0)
    
    return None


def parse_datetime_from_text(text: str, reference_date: Optional[datetime] = None) -> ParsedDateTime:
    """
    Parse completo de data e hora a partir de texto em português.
    
    Args:
        text: Texto contendo data/hora
        reference_date: Data de referência (padrão: agora)
    
    Returns:
        ParsedDateTime com resultado do parsing
    """
    if reference_date is None:
        reference_date = get_current_datetime()
    
    text_lower = text.lower()
    
    # Tentar parsear data
    date_obj = None
    confidence = 1.0
    
    # Tentar datas relativas primeiro
    date_obj = parse_relative_date(text, reference_date)
    if date_obj:
        confidence = 0.95
    
    # Tentar dias da semana
    if not date_obj:
        date_obj = parse_weekday(text, reference_date)
        if date_obj:
            confidence = 0.9
    
    # Tentar datas absolutas
    if not date_obj:
        date_obj = parse_absolute_date(text, reference_date)
        if date_obj:
            confidence = 1.0
    
    # Se não encontrou data, assume hoje
    if not date_obj:
        date_obj = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
        confidence = 0.5
    
    # Tentar parsear hora
    time_tuple = parse_time(text)
    if time_tuple:
        hour, minute = time_tuple
        date_obj = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Se não especificou hora, marca como baixa confiança
        confidence *= 0.7
    
    return ParsedDateTime(
        datetime_obj=date_obj,
        is_valid=True,
        confidence=confidence,
        original_text=text
    )


def validate_datetime(dt: datetime, allow_weekends: bool = False) -> ValidationResult:
    """
    Valida se a data/hora é adequada para agendamento.
    
    Args:
        dt: Data/hora a validar
        allow_weekends: Se permite agendamentos em finais de semana
    
    Returns:
        ValidationResult com resultado da validação
    """
    now = get_current_datetime()
    
    # Verificar se está no passado
    if dt < now:
        return ValidationResult(
            is_valid=False,
            message="A data/hora está no passado. Por favor, escolha uma data futura.",
            suggestions=[]
        )
    
    # Verificar se está muito longe no futuro (mais de 6 meses)
    six_months_ahead = now + timedelta(days=180)
    if dt > six_months_ahead:
        return ValidationResult(
            is_valid=False,
            message="A data está muito distante. Agendamos com até 6 meses de antecedência.",
            suggestions=[]
        )
    
    # Verificar horário comercial (7h às 20h)
    if dt.hour < 7 or dt.hour >= 20:
        suggestions = [
            f"{dt.strftime('%d/%m/%Y')} às 09:00",
            f"{dt.strftime('%d/%m/%Y')} às 14:00",
            f"{dt.strftime('%d/%m/%Y')} às 16:00"
        ]
        return ValidationResult(
            is_valid=False,
            message=f"O horário {dt.strftime('%H:%M')} está fora do horário de atendimento (7h às 20h).",
            suggestions=suggestions
        )
    
    # Verificar final de semana
    if not allow_weekends and dt.weekday() >= 5:  # 5=sábado, 6=domingo
        next_monday = dt + timedelta(days=(7 - dt.weekday()))
        suggestions = [
            f"{next_monday.strftime('%d/%m/%Y')} às 09:00",
            f"{next_monday.strftime('%d/%m/%Y')} às 14:00",
            f"{next_monday.strftime('%d/%m/%Y')} às 16:00"
        ]
        weekday_name = "sábado" if dt.weekday() == 5 else "domingo"
        return ValidationResult(
            is_valid=False,
            message=f"Não atendemos aos {weekday_name}s. Que tal na próxima segunda-feira?",
            suggestions=suggestions
        )
    
    return ValidationResult(
        is_valid=True,
        message="Data/hora válida para agendamento."
    )


def normalize_datetime_string(dt: datetime) -> str:
    """
    Normaliza datetime para string no formato padrão brasileiro.
    
    Args:
        dt: Objeto datetime
    
    Returns:
        String no formato "DD/MM/YYYY HH:MM"
    """
    return dt.strftime("%d/%m/%Y %H:%M")


def extract_datetime_info(text: str) -> Dict[str, Any]:
    """
    Extrai informações de data/hora de um texto e retorna dict completo.
    
    Returns:
        Dict com:
        - datetime_obj: objeto datetime ou None
        - formatted: string formatada ou ""
        - is_valid: bool
        - confidence: float
        - validation_message: str
        - suggestions: list
    """
    parsed = parse_datetime_from_text(text)
    
    if not parsed.datetime_obj:
        return {
            "datetime_obj": None,
            "formatted": "",
            "is_valid": False,
            "confidence": 0.0,
            "validation_message": "Não consegui identificar uma data/hora válida.",
            "suggestions": []
        }
    
    validation = validate_datetime(parsed.datetime_obj)
    
    return {
        "datetime_obj": parsed.datetime_obj,
        "formatted": normalize_datetime_string(parsed.datetime_obj),
        "is_valid": validation.is_valid,
        "confidence": parsed.confidence,
        "validation_message": validation.message,
        "suggestions": validation.suggestions
    }
