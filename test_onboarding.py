"""Test onboarding flow"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_onboarding_flow():
    """Test complete onboarding + appointment flow"""
    session_id = "test_onboarding_001"
    
    print("=" * 60)
    print("TESTE: FLUXO DE ONBOARDING")
    print("=" * 60)
    
    # Step 1: Initial greeting
    print("\n1. Iniciando conversa...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "Oi"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 2: Provide name
    print("2. Fornecendo nome...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "Me chamo João Silva"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 3: Provide phone
    print("3. Fornecendo telefone...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "11987654321"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 4: Provide specialty
    print("4. Fornecendo especialidade...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "dermatologista"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 5: Provide datetime
    print("5. Fornecendo data/hora...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "amanhã às 14h"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 6: Provide mode
    print("6. Fornecendo modo...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "presencial"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Step 7: Confirm
    print("7. Confirmando...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id, "message": "sim"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    print("=" * 60)
    print("TESTE: USUÁRIO RETORNANDO (JÁ CADASTRADO)")
    print("=" * 60)
    
    # New session with same phone
    session_id_2 = "test_returning_001"
    
    print("\n1. Usuário retornando fornece telefone...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": session_id_2, "message": "Meu telefone é 11987654321"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    print("✅ Deve pular onboarding e ir direto para especialidade!")

if __name__ == "__main__":
    test_onboarding_flow()
