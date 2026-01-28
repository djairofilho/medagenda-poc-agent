"""LangGraph state machine for appointment scheduling agent"""
from typing import TypedDict, List, Dict, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.agent.extract import (
    extract_all_fields,
    get_missing_fields,
    detect_intent
)
from app.agent.prompts import (
    GREETING,
    OUT_OF_SCOPE,
    URGENT_NEUTRAL,
    FIELD_REQUESTS,
    format_batched_request,
    format_confirmation,
    format_confirmation_accepted,
    CONFIRMATION_REJECTED
)
from app.agent.tools import (
    is_affirmative,
    is_negative,
    get_last_user_message,
    create_message
)
from app.db.sqlite import insert_appointment


class AgentState(TypedDict):
    """State for the appointment scheduling agent."""
    messages: List[Dict[str, str]]
    extracted: Dict[str, Any]
    missing_fields: List[str]
    awaiting_confirmation: bool
    last_bot_message: str
    appointment_id: Optional[int]
    channel: str
    intent: str  # 'schedule', 'out_of_scope', 'urgent'


def node_extract_fields(state: AgentState) -> AgentState:
    """
    Extract fields from the last user message and detect intent.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with extracted fields and intent
    """
    last_message = get_last_user_message(state['messages'])
    
    # Detect intent
    intent = detect_intent(last_message)
    state['intent'] = intent
    
    # If out of scope or urgent, don't extract fields
    if intent in ['out_of_scope', 'urgent']:
        return state
    
    # Extract fields
    extracted = extract_all_fields(last_message, state['extracted'])
    state['extracted'] = extracted
    
    # Calculate missing fields
    missing = get_missing_fields(extracted)
    state['missing_fields'] = missing
    
    return state


def node_ask_missing_or_confirm(state: AgentState) -> AgentState:
    """
    Ask for missing fields or generate confirmation message.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with bot response
    """
    # Handle out of scope intent
    if state['intent'] == 'out_of_scope':
        state['last_bot_message'] = OUT_OF_SCOPE
        state['intent'] = 'schedule'  # Reset intent
        return state
    
    # Handle urgent intent
    if state['intent'] == 'urgent':
        state['last_bot_message'] = URGENT_NEUTRAL
        state['intent'] = 'schedule'  # Reset intent
        return state
    
    # If there are missing fields, ask for them
    if state['missing_fields']:
        missing = state['missing_fields']
        
        # If only one field missing, ask directly
        if len(missing) == 1:
            field = missing[0]
            state['last_bot_message'] = FIELD_REQUESTS[field]
        else:
            # Batch request for multiple fields
            state['last_bot_message'] = format_batched_request(missing)
        
        return state
    
    # All fields collected, generate confirmation
    state['awaiting_confirmation'] = True
    state['last_bot_message'] = format_confirmation(state['extracted'])
    
    return state


def node_handle_confirmation_and_save(state: AgentState) -> AgentState:
    """
    Handle user confirmation and save appointment to database.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with appointment ID or adjustment request
    """
    if not state['awaiting_confirmation']:
        return state
    
    last_message = get_last_user_message(state['messages'])
    
    # Check for affirmative
    if is_affirmative(last_message):
        # Save to database
        extracted = state['extracted']
        appointment_id = insert_appointment(
            name=extracted['name'],
            phone=extracted['phone'],
            specialty=extracted['specialty'],
            preferred_datetime=extracted['preferred_datetime'],
            mode=extracted['mode'],
            reason=extracted.get('reason'),
            status='confirmed',
            channel=state['channel']
        )
        
        state['appointment_id'] = appointment_id
        state['last_bot_message'] = format_confirmation_accepted(appointment_id)
        state['awaiting_confirmation'] = False
        
        return state
    
    # Check for negative
    if is_negative(last_message):
        state['last_bot_message'] = CONFIRMATION_REJECTED
        state['awaiting_confirmation'] = False
        # Clear extracted fields to allow re-collection
        state['extracted'] = {}
        state['missing_fields'] = []
        
        return state
    
    # Unclear response, ask again
    state['last_bot_message'] = "Por favor, responda 'sim' para confirmar ou 'não' para ajustar."
    
    return state


def should_save(state: AgentState) -> str:
    """
    Determine if we should go to save node or continue asking.
    
    Args:
        state: Current agent state
    
    Returns:
        Next node name
    """
    if state['awaiting_confirmation']:
        return "handle_confirmation"
    
    if state['appointment_id'] is not None:
        return END
    
    return "extract"


def build_graph() -> StateGraph:
    """
    Build the LangGraph state machine.
    
    Returns:
        Compiled state graph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("extract", node_extract_fields)
    workflow.add_node("ask_or_confirm", node_ask_missing_or_confirm)
    workflow.add_node("handle_confirmation", node_handle_confirmation_and_save)
    
    # Set entry point
    workflow.set_entry_point("extract")
    
    # Simple linear flow with conditional routing
    workflow.add_edge("extract", "ask_or_confirm")
    
    # Conditional edge from ask_or_confirm
    def route_from_ask(state: AgentState) -> str:
        if state['awaiting_confirmation']:
            return "handle_confirmation"
        return END
    
    workflow.add_conditional_edges(
        "ask_or_confirm",
        route_from_ask,
        {
            "handle_confirmation": "handle_confirmation",
            END: END
        }
    )
    
    # Always end after handle_confirmation
    workflow.add_edge("handle_confirmation", END)
    
    return workflow.compile()


# Session storage (in-memory for POC)
_sessions: Dict[str, AgentState] = {}


def get_or_create_session(session_id: str, channel: str = "unknown") -> AgentState:
    """
    Get existing session or create a new one.
    
    Args:
        session_id: Session identifier
        channel: Communication channel
    
    Returns:
        Agent state for the session
    """
    if session_id not in _sessions:
        _sessions[session_id] = {
            'messages': [],
            'extracted': {},
            'missing_fields': [],
            'awaiting_confirmation': False,
            'last_bot_message': GREETING,
            'appointment_id': None,
            'channel': channel,
            'intent': 'schedule'
        }
    
    return _sessions[session_id]


def update_session(session_id: str, state: AgentState) -> None:
    """
    Update session state.
    
    Args:
        session_id: Session identifier
        state: Updated agent state
    """
    _sessions[session_id] = state


def reset_session(session_id: str) -> None:
    """
    Reset/delete a session.
    
    Args:
        session_id: Session identifier
    """
    if session_id in _sessions:
        del _sessions[session_id]


def process_message(session_id: str, user_message: str, channel: str = "unknown") -> str:
    """
    Process a user message through the agent graph.
    
    Args:
        session_id: Session identifier
        user_message: User's message
        channel: Communication channel
    
    Returns:
        Bot's response message
    """
    # Get or create session
    state = get_or_create_session(session_id, channel)
    
    # Add user message to state
    state['messages'].append(create_message('user', user_message))
    
    # Build and run graph
    graph = build_graph()
    result = graph.invoke(state)
    
    # Add bot message to state
    bot_message = result['last_bot_message']
    result['messages'].append(create_message('assistant', bot_message))
    
    # Update session
    update_session(session_id, result)
    
    return bot_message
