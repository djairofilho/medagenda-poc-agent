from app.agent.state import AgentState
from app.agent.agents.triage.prompt import TRIAGE_PROMPT
from app.agent.agents.triage.tools import check_emergency, get_emergency_contact
from app.agent.utils import get_llm
from langchain_core.messages import SystemMessage, AIMessage

def triage_node(state: AgentState):
    """
    Handler for Triage Intent.
    """
    messages = state['messages']
    last_user_msg = messages[-1].content if messages else ""
    
    # 1. Check Hard Rules (Emergency)
    if check_emergency(last_user_msg):
        contact = get_emergency_contact()
        alert_msg = f"⚠️ ISSO PODE SER UMA EMERGÊNCIA.\nPor favor, não espere atendimento aqui.\n\n{contact}\n\nSe desloque para o hospital mais próximo agora."
        return {
            "messages": [AIMessage(content=alert_msg)],
            "current_agent": "triage"
        }

    # 2. LLM Handler for refusal/guidance
    llm = get_llm()
    prompt = [SystemMessage(content=TRIAGE_PROMPT)] + messages
    response = llm.invoke(prompt)
    
    return {
        "messages": [response],
        "current_agent": "triage"
    }
