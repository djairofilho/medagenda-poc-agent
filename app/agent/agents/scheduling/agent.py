from app.agent.state import AgentState
from app.agent.agents.scheduling.prompt import SCHEDULING_PROMPT
from app.agent.agents.scheduling.tools import check_availability
from app.agent.utils import get_llm
from langchain_core.messages import SystemMessage

def scheduling_node(state: AgentState):
    """
    Handler for Scheduling Intent.
    """
    llm = get_llm()
    messages = state['messages']
    
    # Construct prompt
    prompt = [SystemMessage(content=SCHEDULING_PROMPT)] + messages
    
    # Invoke LLM
    response = llm.invoke(prompt)
    
    return {
        "messages": [response],
        "current_agent": "scheduling"
    }
