from typing import TypedDict, Annotated, List, Optional, Any
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    State of the agent conversation.
    """
    messages: Annotated[List[Any], add_messages]
    user_id: Optional[str]
    next_node: Optional[str]
    slots: dict
    
    # Compatibility with main.py
    extracted: dict
    missing_fields: list
    appointment_id: Optional[Any]
    intent: Optional[str]

    waiting_confirmation: bool
    current_agent: Optional[str]
