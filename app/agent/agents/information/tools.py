import json
from pathlib import Path
from app.db.availability import list_available_slots
from datetime import datetime

def load_clinic_info() -> str:
    """
    Load JSON data and available slots to inject into context.
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
    info_text += "HORÁRIO DE FUNCIONAMENTO: Seg-Sex 08h às 20h.\n"
    
    # Add Available Slots from DB
    try:
        # Get slots for today and next 7 days
        today_str = datetime.now().strftime("%Y-%m-%d")
        slots = list_available_slots() # Get all available for now
        
        if slots:
            info_text += "\nPRÓXIMOS HORÁRIOS DISPONÍVEIS NO SISTEMA:\n"
            # Limit to first 15 slots to avoid too much context
            for slot in slots[:15]:
                dt_obj = datetime.strptime(slot['slot_datetime'], "%Y-%m-%d %H:%M")
                info_text += f"- {slot['specialty']}: {dt_obj.strftime('%d/%m/%Y %H:%M')}\n"
        else:
            info_text += "\nNo momento não há horários específicos pré-agendados no sistema. Informe a especialidade e preferência para verificarmos.\n"
    except Exception as e:
        info_text += f"\nErro ao carregar horários disponíveis: {str(e)}\n"
    
    return info_text
