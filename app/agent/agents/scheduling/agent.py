from app.agent.state import AgentState
from app.agent.agents.scheduling.prompt import SCHEDULING_PROMPT
from app.agent.agents.scheduling.tools import check_availability
from app.agent.utils import get_llm
from app.db.availability import list_available_slots
from langchain_core.messages import SystemMessage
from datetime import datetime

def scheduling_node(state: AgentState):
    """
    Handler for Scheduling Intent.
    """
    llm = get_llm()
    messages = state['messages']
    
    now = datetime.now()
    current_date_info = f"\nDATA ATUAL: {now.strftime('%d/%m/%Y')} ({now.strftime('%A')})"
    
    # Get dynamic slots to help the agent know what is available
    try:
        slots = list_available_slots()
        slots_text = "\n\nHORÁRIOS DISPONÍVEIS NO SISTEMA (REAIS):\n"
        if slots:
            for s in slots[:10]:
                slots_text += f"- {s['specialty']}: {s['slot_datetime']}\n"
        else:
            slots_text += "Nenhum horário específico cadastrado. Siga as regras de horário padrão.\n"
    except Exception:
        slots_text = ""

    # Construct prompt with real availability data
    full_prompt = SCHEDULING_PROMPT + current_date_info + slots_text
    prompt = [SystemMessage(content=full_prompt)] + messages
    
    # Invoke LLM
    response = llm.invoke(prompt)
    
    return {
        "messages": [response],
        "current_agent": "scheduling"
    }
