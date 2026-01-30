"""
Teste rápido para verificar se o agente aceita CPF corretamente.
"""

from app.agent.graph import process_message, reset_session

def test_cpf_collection():
    """Testa se o agente coleta CPF sem recusar."""
    
    session_id = "test_cpf_session"
    reset_session(session_id)
    
    print("=" * 70)
    print("TESTE: Coleta de CPF no Agendamento")
    print("=" * 70)
    
    # Simulação de conversa
    conversas = [
        "Quero agendar cardiologista para amanhã às 14h",
        "Sim, confirmo",
        "João Silva, CPF 12345678901"
    ]
    
    for i, mensagem in enumerate(conversas, 1):
        print(f"\n{'─' * 70}")
        print(f"👤 Usuário (mensagem {i}): {mensagem}")
        print(f"{'─' * 70}")
        
        resposta = process_message(session_id, mensagem)
        
        print(f"🤖 MedAgenda: {resposta}")
        
        # Verificar se não há recusa de CPF
        if "não posso processar" in resposta.lower() or "não posso armazenar" in resposta.lower():
            print("\n❌ ERRO: Bot recusou coletar CPF!")
            return False
    
    print("\n" + "=" * 70)
    print("✅ TESTE PASSOU: Bot aceitou CPF corretamente!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    test_cpf_collection()
