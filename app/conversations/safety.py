"""Conservative, deterministic emergency interception before LLM routing."""

import unicodedata


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


EMERGENCY_PHRASES = (
    "dor no peito", "falta de ar", "dificuldade para respirar", "nao consigo respirar",
    "desmaio", "desmaiou", "hemorragia", "sangramento intenso", "estou sangrando muito",
    "infarto", "avc", "convulsao", "ingeriu veneno", "bebeu veneno", "bebeu candida",
    "ingeriu agua sanitaria", "estou morrendo",
)


def is_emergency(text: str) -> bool:
    folded = _fold(text)
    return any(phrase in folded for phrase in EMERGENCY_PHRASES)


EMERGENCY_REPLY = (
    "Isso pode ser uma emergência. Não espere atendimento por aqui. "
    "Ligue para o SAMU (192) ou procure um pronto-socorro imediatamente."
)
