from datetime import datetime, timedelta
import random


def check_availability(specialty: str, dt: datetime) -> tuple[bool, str]:
    """
    Mock checking availability with proper datetime validation.
    
    Args:
        specialty: Especialidade médica
        dt: Objeto datetime
    
    Returns:
        Tupla (is_available, message)
    """
    # Verificar horário comercial (7h às 20h)
    if dt.hour < 7 or dt.hour >= 20:
        return False, f"Horário {dt.strftime('%H:%M')} fora do expediente (7h-20h)"
    
    # Verificar final de semana
    if dt.weekday() >= 5:
        weekday_name = "sábado" if dt.weekday() == 5 else "domingo"
        return False, f"Não atendemos aos {weekday_name}s"
    
    # Mock: sempre disponível se passar as validações
    # Em produção, verificaria banco de dados real
    return True, "Horário disponível"


def suggest_next_slots(specialty: str, base_date: datetime = None) -> list[str]:
    """
    Return mock next available slots.
    
    Args:
        specialty: Especialidade médica
        base_date: Data base para sugestões (padrão: amanhã)
    
    Returns:
        Lista de horários formatados
    """
    if base_date is None:
        base_date = datetime.now() + timedelta(days=1)
    
    # Garantir que é dia útil
    while base_date.weekday() >= 5:
        base_date += timedelta(days=1)
    
    return [
        base_date.replace(hour=9, minute=0).strftime("%d/%m/%Y %H:%M"),
        base_date.replace(hour=14, minute=0).strftime("%d/%m/%Y %H:%M"),
        base_date.replace(hour=16, minute=0).strftime("%d/%m/%Y %H:%M")
    ]


def book_appointment_mock(name: str, cpf: str, specialty: str, dt: datetime) -> dict:
    """
    Mock booking action.
    
    Args:
        name: Nome do paciente
        cpf: CPF do paciente
        specialty: Especialidade
        dt: Data/hora do agendamento
    
    Returns:
        Dict com detalhes do agendamento
    """
    return {
        "id": random.randint(1000, 9999),
        "status": "confirmed",
        "details": f"{specialty} em {dt.strftime('%d/%m/%Y às %H:%M')}",
        "patient": name,
        "datetime": dt.isoformat()
    }
