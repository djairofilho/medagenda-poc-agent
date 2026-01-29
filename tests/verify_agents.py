import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(project_root) / ".env")

from app.agent.graph import process_message, reset_session
import time

def run_test():
    print("=== STARTING VERIFICATION ===\n")
    
    scenarios = [
        ("Cenário 1: Agendamento", "Quero marcar um cardiologista para amanhã"),
        ("Cenário 2: Triagem (Emergência)", "Socorro, meu pai está com dor no peito e falta de ar"),
        ("Cenário 3: Triagem (Dúvida Médica)", "Estou com uma mancha vermelha, o que pode ser?"),
        ("Cenário 4: Informação (Endereço)", "Qual o endereço da clínica?"),
        ("Cenário 5: Informação (Convênio)", "Vocês aceitam Unimed?")
    ]

    for title, msg in scenarios:
        print(f"\n--- {title} ---")
        session_id = f"test_{int(time.time())}"
        print(f"User: {msg}")
        try:
            response = process_message(session_id, msg)
            print(f"Bot: {response}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
