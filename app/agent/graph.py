import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agent.state import AgentState
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.utils import get_llm

# Import Agent Nodes
from app.agent.agents.scheduling.agent import scheduling_node
from app.agent.agents.triage.agent import triage_node
from app.agent.agents.information.agent import information_node

# Session Storage
_sessions: Dict[str, AgentState] = {}

def get_or_create_session(session_id: str, channel: str = "web") -> AgentState:
    """Get or initialize session state."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "messages": [],
            "user_id": session_id,
            "next_node": None,
            "slots": {},
            "extracted": {},  # Compat
            "missing_fields": [], # Compat
            "appointment_id": None, # Compat
            "intent": None, # Compat
            "waiting_confirmation": False,
            "current_agent": None
        }
    return _sessions[session_id]

def reset_session(session_id: str):
    """Clear session history."""
    if session_id in _sessions:
        del _sessions[session_id]

def router_node(state: AgentState):
    """
    Router / Supervisor Node.
    Analyzes the conversation history and SYSTEM PROMPT to decide the next agent.
    """
    llm = get_llm()
    messages = state['messages']
    
    # We ask the LLM to decide the category
    # For robust routing, we might force a structured output or specific keyword.
    # Here we simulate with a prompt.
    
    routing_instructions = (
        "\nBased on the user's last message and history, verify which agent should handle this:"
        "\n- 'scheduling': For appointments (marcar, agendar, cancelar)"
        "\n- 'triage': For symptoms, pain, emergencies (dor, febre, doente, remedio)"
        "\n- 'information': For address, prices, questions (onde fica, valor, convenio)"
        "\n\nRespond ONLY with one word: scheduling, triage, or information."
    )
    
    # Create a temporary routing prompt
    cmd_messages = [SystemMessage(content=SYSTEM_PROMPT + routing_instructions)] + messages
    
    response = llm.invoke(cmd_messages)
    decision = response.content.strip().lower()
    
    # Clean decision
    if "triage" in decision or "emerg" in decision or "dor" in decision:
        return {"next_node": "triage", "intent": "triage"}
    elif "schedul" in decision or "agend" in decision:
        return {"next_node": "scheduling", "intent": "schedule"}
    elif "info" in decision or "enderec" in decision or "onde" in decision:
        return {"next_node": "information", "intent": "info"}
    else:
        # Default fallback
        return {"next_node": "information", "intent": "info"}

def build_graph():
    """Build the StateGraph."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("scheduling", scheduling_node)
    workflow.add_node("triage", triage_node)
    workflow.add_node("information", information_node)
    
    # Entry Point
    workflow.set_entry_point("router")
    
    # Conditional Edges from Router
    workflow.add_conditional_edges(
        "router",
        lambda state: state['next_node'],
        {
            "scheduling": "scheduling",
            "triage": "triage",
            "information": "information"
        }
    )
    
    # Edges from Agents -> END (Single turn per request for this POC)
    # In a real conversation loop, we might loop back to router or wait for user.
    # Here, 'process_message' handles one turn.
    workflow.add_edge("scheduling", END)
    workflow.add_edge("triage", END)
    workflow.add_edge("information", END)
    
    return workflow.compile()

def process_message(session_id: str, user_message: str, channel: str = "web") -> str:
    """
    Main entry point for the API.
    """
    state_schema = get_or_create_session(session_id, channel)
    
    # Add User Message to History
    # NOTE: AgentState uses add_messages (append), but our local dict is just a list.
    # LangGraph handles 'messages' list operations if managed by LangGraph memory,
    # but here we are managing _sessions manualy. 
    # We manually append to be safe before invoking.
    state_schema["messages"].append(HumanMessage(content=user_message))
    
    # Invoke Graph
    app = build_graph()
    result = app.invoke(state_schema)
    
    # Get last message (Assistant)
    last_msg = result["messages"][-1]
    response_text = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
    
    # Update Session State
    # Note: 'result' contains the full updated state
    _sessions[session_id] = result
    
    return response_text
