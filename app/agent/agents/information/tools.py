import json
import os
from pathlib import Path

def load_clinic_info() -> str:
    """
    Load JSON data to inject into context.
    """
    base_path = Path(__file__).resolve().parent.parent.parent / "data"
    
    info_text = ""
    
    # Load Insurance
    try:
        with open(base_path / "insurance.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            info_text += f"\nCONVÊNIOS ACEITOS: {', '.join(data.get('accepted_plans', []))}\n"
            info_text += f"Obs: {data.get('notes')}\n"
    except Exception:
        info_text += "Erro ao carregar lista de convênios.\n"

    # Load Exam Prep
    try:
        with open(base_path / "exam_prep.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            info_text += "\nPREPARO DE EXAMES:\n"
            for k, v in data.items():
                info_text += f"- {k}: {v}\n"
    except Exception:
        pass
        
    # Add static info (could be moved to json too)
    info_text += "\nENDEREÇO: Av. Paulista, 1000 - São Paulo/SP\n"
    info_text += "HORÁRIO: Seg-Sex 08h às 20h.\n"
    
    return info_text
