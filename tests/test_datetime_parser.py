"""
Testes para o módulo datetime_parser.
Valida parsing de diferentes formatos de data/hora em português brasileiro.
"""

from datetime import datetime
from app.agent.datetime_parser import (
    parse_datetime_from_text,
    validate_datetime,
    extract_datetime_info,
    normalize_datetime_string
)


def test_relative_dates():
    """Testa parsing de datas relativas."""
    print("\n=== TESTE: Datas Relativas ===")
    
    test_cases = [
        "Quero agendar para amanhã às 14h",
        "Pode ser hoje à tarde",
        "Depois de amanhã de manhã",
        "Daqui a 3 dias às 16h",
        "Daqui a 2 semanas"
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Confiança: {result['confidence']:.2f}")
        if not result['is_valid']:
            print(f"  Mensagem: {result['validation_message']}")


def test_weekdays():
    """Testa parsing de dias da semana."""
    print("\n\n=== TESTE: Dias da Semana ===")
    
    test_cases = [
        "Próxima segunda às 10h",
        "Terça-feira de manhã",
        "Na sexta às 15:30",
        "Segunda que vem às 9h"
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Confiança: {result['confidence']:.2f}")


def test_absolute_dates():
    """Testa parsing de datas absolutas."""
    print("\n\n=== TESTE: Datas Absolutas ===")
    
    test_cases = [
        "15/03 às 10:30",
        "20/02/2026 às 14h",
        "15 de março às 16h",
        "10 de abril de 2026 às 9h30"
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Confiança: {result['confidence']:.2f}")


def test_time_formats():
    """Testa diferentes formatos de hora."""
    print("\n\n=== TESTE: Formatos de Hora ===")
    
    test_cases = [
        "Amanhã às 14:30",
        "Amanhã às 14h30",
        "Amanhã às 14h",
        "Amanhã de manhã",
        "Amanhã à tarde",
        "Amanhã à noite",
        "Amanhã ao meio-dia"
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Confiança: {result['confidence']:.2f}")


def test_validation():
    """Testa validação de datas/horas."""
    print("\n\n=== TESTE: Validação ===")
    
    test_cases = [
        "Hoje às 5h",  # Muito cedo
        "Amanhã às 22h",  # Muito tarde
        "Próximo sábado às 10h",  # Final de semana
        "Amanhã às 14h",  # Válido
        "15/03/2026 às 10h"  # Válido
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Mensagem: {result['validation_message']}")
        if result['suggestions']:
            print(f"  Sugestões: {', '.join(result['suggestions'][:2])}")


def test_edge_cases():
    """Testa casos extremos."""
    print("\n\n=== TESTE: Casos Extremos ===")
    
    test_cases = [
        "Quero agendar cardiologista",  # Sem data/hora
        "Pode ser qualquer dia",  # Vago
        "Amanhã",  # Sem hora
        "Às 14h",  # Sem data
        "15/13/2026 às 10h"  # Data inválida
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  Data/Hora: {result['formatted']}")
        print(f"  Válido: {result['is_valid']}")
        print(f"  Confiança: {result['confidence']:.2f}")


def test_real_conversations():
    """Testa casos de conversas reais."""
    print("\n\n=== TESTE: Conversas Reais ===")
    
    test_cases = [
        "Oi, preciso marcar um cardiologista para amanhã às 14h",
        "Queria agendar com o Dr. Silva na próxima segunda de manhã",
        "Tem vaga para 15/03 às 10:30?",
        "Pode ser depois de amanhã à tarde?",
        "Prefiro na sexta às 16h"
    ]
    
    for text in test_cases:
        result = extract_datetime_info(text)
        print(f"\nTexto: '{text}'")
        print(f"  ✓ Data/Hora: {result['formatted']}")
        print(f"  ✓ Válido: {'Sim' if result['is_valid'] else 'Não'}")
        print(f"  ✓ Confiança: {result['confidence']:.0%}")
        if not result['is_valid']:
            print(f"  ⚠ Problema: {result['validation_message']}")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DO MÓDULO DATETIME_PARSER")
    print("=" * 60)
    
    test_relative_dates()
    test_weekdays()
    test_absolute_dates()
    test_time_formats()
    test_validation()
    test_edge_cases()
    test_real_conversations()
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)
