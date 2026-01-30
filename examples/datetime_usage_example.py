"""
Exemplo de uso do módulo datetime_parser no contexto do agente de agendamento.
Demonstra como integrar o parsing de data/hora no fluxo de conversação.
"""

from app.agent.datetime_parser import extract_datetime_info, validate_datetime
from app.agent.agents.scheduling.tools import check_availability, suggest_next_slots


def exemplo_fluxo_agendamento():
    """Simula um fluxo completo de agendamento com parsing de data/hora."""
    
    print("=" * 70)
    print("EXEMPLO: Fluxo de Agendamento com Validação de Data/Hora")
    print("=" * 70)
    
    # Simulação de mensagens do usuário
    mensagens_usuario = [
        "Quero agendar cardiologista para amanhã às 14h",
        "Preciso marcar consulta na próxima segunda de manhã",
        "Tem vaga para 15/03 às 10:30?",
        "Pode ser sábado às 10h?",  # Final de semana - deve sugerir alternativa
        "Quero agendar para hoje às 22h",  # Fora do horário - deve sugerir alternativa
    ]
    
    for i, mensagem in enumerate(mensagens_usuario, 1):
        print(f"\n{'─' * 70}")
        print(f"EXEMPLO {i}")
        print(f"{'─' * 70}")
        print(f"👤 Usuário: {mensagem}")
        print()
        
        # 1. Extrair data/hora da mensagem
        info = extract_datetime_info(mensagem)
        
        print(f"📅 Data/Hora Extraída: {info['formatted']}")
        print(f"🎯 Confiança: {info['confidence']:.0%}")
        print(f"✓ Válido: {'Sim' if info['is_valid'] else 'Não'}")
        
        # 2. Se não for válido, mostrar mensagem e sugestões
        if not info['is_valid']:
            print(f"⚠️  Problema: {info['validation_message']}")
            if info['suggestions']:
                print(f"💡 Sugestões:")
                for sug in info['suggestions'][:3]:
                    print(f"   • {sug}")
            print(f"\n🤖 Bot: {info['validation_message']}")
            if info['suggestions']:
                print(f"       Que tal um destes horários?")
                for sug in info['suggestions'][:3]:
                    print(f"       • {sug}")
        else:
            # 3. Se válido, verificar disponibilidade
            dt = info['datetime_obj']
            disponivel, msg = check_availability("Cardiologia", dt)
            
            if disponivel:
                print(f"✅ Disponibilidade: {msg}")
                print(f"\n🤖 Bot: Perfeito! Vou agendar Cardiologia para **{info['formatted']}**.")
                print(f"       Confirma? 👍")
            else:
                print(f"❌ Disponibilidade: {msg}")
                slots = suggest_next_slots("Cardiologia", dt)
                print(f"\n🤖 Bot: {msg}. Que tal um destes horários?")
                for slot in slots:
                    print(f"       • {slot}")


def exemplo_casos_especificos():
    """Demonstra casos específicos de parsing."""
    
    print("\n\n" + "=" * 70)
    print("EXEMPLOS: Casos Específicos de Parsing")
    print("=" * 70)
    
    casos = [
        ("Datas Relativas", [
            "amanhã às 14h",
            "depois de amanhã de manhã",
            "daqui a 3 dias às 16h"
        ]),
        ("Dias da Semana", [
            "próxima segunda às 10h",
            "terça-feira à tarde",
            "sexta às 15:30"
        ]),
        ("Datas Absolutas", [
            "15/03 às 10:30",
            "20 de fevereiro às 14h",
            "10/04/2026 às 9h"
        ]),
        ("Períodos do Dia", [
            "amanhã de manhã",
            "amanhã à tarde",
            "amanhã à noite",
            "amanhã ao meio-dia"
        ])
    ]
    
    for categoria, exemplos in casos:
        print(f"\n{'─' * 70}")
        print(f"📋 {categoria}")
        print(f"{'─' * 70}")
        
        for texto in exemplos:
            info = extract_datetime_info(texto)
            status = "✅" if info['is_valid'] else "❌"
            print(f"{status} '{texto}'")
            print(f"   → {info['formatted']} (confiança: {info['confidence']:.0%})")


if __name__ == "__main__":
    exemplo_fluxo_agendamento()
    exemplo_casos_especificos()
    
    print("\n" + "=" * 70)
    print("✨ Exemplos concluídos!")
    print("=" * 70)
