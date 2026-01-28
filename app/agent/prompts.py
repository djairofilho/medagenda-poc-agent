"""Standard prompts and messages for the agent"""

# Greeting message
GREETING = """Oi! Eu sou o medAgenda 😊

Posso te ajudar a marcar uma consulta. Você já sabe a especialidade que precisa?"""

# Out of scope response (medical advice requests)
OUT_OF_SCOPE = """Eu só ajudo a marcar consulta. Você quer agendar com qual especialidade?"""

# Urgent neutral response
URGENT_NEUTRAL = """Posso ajudar a agendar, mas se você considerar urgente procure atendimento imediato.

Qual especialidade você gostaria de agendar?"""

# Field request messages
FIELD_REQUESTS = {
    'name': 'Qual é o seu nome completo?',
    'phone': 'Qual é o seu WhatsApp/telefone?',
    'specialty': 'Qual especialidade você precisa? (ex: dermatologista, cardiologista, clínico geral)',
    'preferred_datetime': 'Qual seria o melhor dia e horário para você?',
    'mode': 'Você prefere atendimento presencial ou online?',
}

# Batched request template
BATCHED_REQUEST_TEMPLATE = """Para finalizar o agendamento, preciso de algumas informações:

{fields}

Pode me passar esses dados?"""

# Confirmation template
CONFIRMATION_TEMPLATE = """Perfeito! Vou confirmar os dados da sua consulta:

📋 **Nome:** {name}
📱 **Telefone:** {phone}
🏥 **Especialidade:** {specialty}
📅 **Data/Horário:** {preferred_datetime}
📍 **Modalidade:** {mode}
{reason_line}

Está tudo certo? Confirmar? (sim/não)"""

# Confirmation accepted
CONFIRMATION_ACCEPTED = """✅ Consulta agendada com sucesso!

**Número do agendamento:** #{appointment_id}

Em breve você receberá a confirmação. Obrigado! 😊"""

# Confirmation rejected
CONFIRMATION_REJECTED = """Ok! O que você gostaria de ajustar?"""

# Generic error
GENERIC_ERROR = """Desculpe, ocorreu um erro. Vamos tentar novamente?"""


def format_batched_request(missing_fields: list) -> str:
    """
    Format a batched request for multiple missing fields.
    
    Args:
        missing_fields: List of missing field names
    
    Returns:
        Formatted message requesting the fields
    """
    field_lines = []
    for i, field in enumerate(missing_fields, 1):
        field_lines.append(f"{i}. {FIELD_REQUESTS[field]}")
    
    fields_text = '\n'.join(field_lines)
    return BATCHED_REQUEST_TEMPLATE.format(fields=fields_text)


def format_confirmation(extracted: dict) -> str:
    """
    Format confirmation message with extracted data.
    
    Args:
        extracted: Dictionary of extracted fields
    
    Returns:
        Formatted confirmation message
    """
    reason_line = ''
    if extracted.get('reason'):
        reason_line = f"\n💬 **Motivo:** {extracted['reason']}"
    
    return CONFIRMATION_TEMPLATE.format(
        name=extracted['name'],
        phone=extracted['phone'],
        specialty=extracted['specialty'],
        preferred_datetime=extracted['preferred_datetime'],
        mode=extracted['mode'],
        reason_line=reason_line
    )


def format_confirmation_accepted(appointment_id: int) -> str:
    """
    Format confirmation accepted message with appointment ID.
    
    Args:
        appointment_id: The created appointment ID
    
    Returns:
        Formatted success message
    """
    return CONFIRMATION_ACCEPTED.format(appointment_id=appointment_id)
