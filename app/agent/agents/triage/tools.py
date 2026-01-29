def check_emergency(text: str) -> bool:
    """
    Check for emergency keywords in the text.
    """
    keywords = [
        "desmaio", "desmaiou", 
        "sangue", "sangrando", "hemorragia",
        "falta de ar", "sufocado", "dificuldade para respirar",
        "dor no peito", "dor no coração", "taquicardia", "infarto",
        "ingeriu veneno", "bebeu veneno",
        "pancada na cabeça", "traumatismo",
        "socorro", "estou morrendo"
    ]
    
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            return True
    return False

def get_emergency_contact() -> str:
    """Return emergency contact info."""
    return "SAMU: 192 | Bombeiros: 193 | Hospital Mais Próximo: (11) 5555-0000"
