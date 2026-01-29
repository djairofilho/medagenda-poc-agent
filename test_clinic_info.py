"""Test clinic info flow"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_clinic_info():
    """Test clinic information requests"""
    print("=" * 60)
    print("TESTE: SOLICITAÇÃO DE INFORMAÇÕES DA CLÍNICA")
    print("=" * 60)
    
    # Test 1: Address
    print("\n1. Perguntando endereço...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": "test_info_001", "message": "Qual é o endereço da clínica?"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Test 2: Hours
    print("2. Perguntando horário...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": "test_info_002", "message": "Qual o horário de funcionamento?"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Test 3: Services
    print("3. Perguntando serviços...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": "test_info_003", "message": "Quais especialidades vocês atendem?"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Test 4: General info
    print("4. Pergunta genérica...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": "test_info_004", "message": "Me dá informações da clínica"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    # Test 5: Parking
    print("5. Perguntando sobre estacionamento...")
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"session_id": "test_info_005", "message": "Tem estacionamento?"}
    )
    data = response.json()
    print(f"Bot: {data['reply']}\n")
    
    print("=" * 60)
    print("✅ Testes de informações concluídos!")
    print("=" * 60)

if __name__ == "__main__":
    test_clinic_info()
