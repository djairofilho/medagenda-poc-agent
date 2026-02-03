from app.agent.state import AgentState
from app.agent.agents.information.prompt import INFO_PROMPT
from app.agent.agents.information.tools import load_clinic_info
from app.agent.utils import get_llm
from langchain_core.messages import SystemMessage

def information_node(state: AgentState):
    """
    Handler for Information Intent.
    """
    llm = get_llm()
    messages = state['messages']
    
    # Load Context
    context_data = load_clinic_info()
    from datetime import datetime
    now = datetime.now()
    date_info = f"\nDATA ATUAL: {now.strftime('%d/%m/%Y')} ({now.strftime('%A')})"
    
    formatted_prompt = INFO_PROMPT.format(context_data=context_data) + date_info
    
    # Construct prompt
    prompt = [SystemMessage(content=formatted_prompt)] + messages
    
    # Invoke LLM
    response = llm.invoke(prompt)
    
    return {
        "messages": [response],
        "current_agent": "information"
    }
