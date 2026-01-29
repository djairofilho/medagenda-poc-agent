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
    
    # Onboarding fields
    patient_id: Optional[int]  # ID if patient exists
    is_onboarded: bool  # True if patient already registered
    onboarding_step: str  # 'name', 'phone', 'complete'


def node_extract_fields(state: AgentState) -> AgentState:
    """
    Extract fields from the last user message using PydanticAI + regex merge.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with extracted fields and intent
    """
    last_message = get_last_user_message(state['messages'])
    
    # 1. Extract via PydanticAI (structured LLM extraction)
    from app.agent.extractor import extract_with_pydantic_ai
    from app.agent.extractor.merge import merge_extractions
    
    llm_result = extract_with_pydantic_ai(last_message)
    
    # 2. Extract via regex (fallback/complement)
    # IMPORTANT: Pass current extracted state to preserve data across messages
    regex_result = extract_all_fields(last_message, state['extracted'])
    
    # 3. Merge: regex wins phone/mode, LLM wins semantic fields
    merged = merge_extractions(llm_result, regex_result)
    
    # 4. Update state with flags from LLM
    if merged.out_of_scope:
        state['intent'] = 'out_of_scope'
    elif merged.urgent_flag:
        state['intent'] = 'urgent'
    else:
        state['intent'] = 'schedule'
    
    # 5. Convert ExtractResult to dict for compatibility
    state['extracted'] = merged.to_dict()
    
    # 6. Calculate missing fields
    missing = get_missing_fields(state['extracted'])
    state['missing_fields'] = missing
    
    return state


def node_check_onboarding(state: AgentState) -> AgentState:
    """
    Check if user is already onboarded (registered).
    If phone is provided, check database for existing patient.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with onboarding status
    """
    from app.db.sqlite import get_patient_by_phone
    
    phone = state['extracted'].get('phone')
    
    # If we have a phone, check if patient exists
    if phone:
        patient = get_patient_by_phone(phone)
        
        if patient:
            # Patient exists! Load their data
            state['is_onboarded'] = True
            state['patient_id'] = patient['id']
            state['onboarding_step'] = 'complete'
            
            # Fill name from database if not provided in message
            if not state['extracted'].get('name'):
                state['extracted']['name'] = patient['name']
                # Recalculate missing fields
                missing = get_missing_fields(state['extracted'])
                state['missing_fields'] = missing
            
            print(f"[Onboarding] Patient found: {patient['name']} ({phone})")
        else:
            # New patient - needs onboarding
            state['is_onboarded'] = False
            state['patient_id'] = None
            state['onboarding_step'] = 'name' if not state['extracted'].get('name') else 'phone'
            
            print(f"[Onboarding] New patient with phone: {phone}")
    else:
        # No phone yet - definitely needs onboarding
        state['is_onboarded'] = False
        state['patient_id'] = None
        state['onboarding_step'] = 'name' if not state['extracted'].get('name') else 'phone'
        
        print(f"[Onboarding] No phone provided, starting onboarding")
    
    return state


def node_provide_clinic_info(state: AgentState) -> AgentState:
    """
    Provide clinic information based on user query.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with clinic information
    """
    from app.db.sqlite import get_all_clinic_info
    
    last_message = get_last_user_message(state['messages'])
    text_lower = last_message.lower()
    
    # Get all clinic info
    clinic_info = get_all_clinic_info()
    
    # Determine what specific info user is asking for
    response_parts = []
    
    # Address
    if any(word in text_lower for word in ['endereço', 'endereco', 'onde', 'localização', 'localizacao', 'chegar']):
        response_parts.append(f"📍 **Endereço:**\n{clinic_info.get('address', 'Não disponível')}")
    
    # Hours
    if any(word in text_lower for word in ['horário', 'horario', 'funciona', 'abre', 'fecha', 'atendimento']):
        response_parts.append(f"🕐 **Horário de Funcionamento:**\n{clinic_info.get('hours', 'Não disponível')}")
    
    # Services/Specialties
    if any(word in text_lower for word in ['serviços', 'servicos', 'especialidades', 'atende']):
        response_parts.append(f"🏥 **Serviços:**\n{clinic_info.get('services', 'Não disponível')}")
    
    # Insurance
    if any(word in text_lower for word in ['convênio', 'convenio', 'plano']):
        response_parts.append(f"💳 **Convênios:**\n{clinic_info.get('insurance', 'Não disponível')}")
    
    # Parking
    if 'estacionamento' in text_lower:
        response_parts.append(f"🚗 **Estacionamento:**\n{clinic_info.get('parking', 'Não disponível')}")
    
    # Accessibility
    if 'acessibilidade' in text_lower or 'cadeirante' in text_lower:
        response_parts.append(f"♿ **Acessibilidade:**\n{clinic_info.get('accessibility', 'Não disponível')}")
    
    # Contact
    if any(word in text_lower for word in ['telefone', 'contato', 'whatsapp']):
        phone = clinic_info.get('phone', '')
        whatsapp = clinic_info.get('whatsapp', '')
        response_parts.append(f"📞 **Contato:**\nTelefone: {phone}\nWhatsApp: {whatsapp}")
    
    # If no specific info detected, provide general info
    if not response_parts:
        name = clinic_info.get('name', 'Clínica MedAgenda')
        response_parts = [
            f"**{name}**\n",
            f"📍 {clinic_info.get('address', 'Não disponível')}",
            f"🕐 {clinic_info.get('hours', 'Não disponível')}",
            f"📞 Telefone: {clinic_info.get('phone', 'Não disponível')}",
            f"📱 WhatsApp: {clinic_info.get('whatsapp', 'Não disponível')}"
        ]
    
    # Build response
    info_response = "\n\n".join(response_parts)
    info_response += "\n\n✨ Posso te ajudar a agendar uma consulta?"
    
    state['last_bot_message'] = info_response
    state['intent'] = 'schedule'  # Reset to schedule after providing info
    
    return state



def node_ask_missing_or_confirm(state: AgentState) -> AgentState:
    """
    Ask for missing fields or generate confirmation message.
    Handles onboarding (name/phone) separately from appointment scheduling.
    
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
    
    # ========================================================================
    # ONBOARDING FLOW (if not onboarded)
    # ========================================================================
    if not state.get('is_onboarded', False):
        # Ask for name first
        if not state['extracted'].get('name'):
            state['last_bot_message'] = "Qual é o seu nome completo?"
            return state
        
        # Then ask for phone
        if not state['extracted'].get('phone'):
            state['last_bot_message'] = "Qual é o seu WhatsApp ou telefone?"
            return state
        
        # Both name and phone collected - save patient
        from app.db.sqlite import create_patient
        
        patient_id = create_patient(
            name=state['extracted']['name'],
            phone=state['extracted']['phone'],
            channel=state['channel']
        )
        
        state['patient_id'] = patient_id
        state['is_onboarded'] = True
        state['onboarding_step'] = 'complete'
        
        print(f"[Onboarding] Patient created: {state['extracted']['name']} (ID: {patient_id})")
        
        # Welcome message and proceed to appointment
        state['last_bot_message'] = (
            f"Prazer em conhecê-lo(a), {state['extracted']['name']}! 😊\n\n"
            "Agora vamos agendar sua consulta.\n\n"
            "Qual especialidade você precisa? (ex: dermatologista, cardiologista, clínico geral)"
        )
        return state
    
    # ========================================================================
    # APPOINTMENT SCHEDULING FLOW (onboarded users)
    # ========================================================================
    
    # Define appointment-specific required fields (name/phone already have)
    appointment_fields = ['specialty', 'preferred_datetime', 'mode']
    appointment_missing = [f for f in appointment_fields if not state['extracted'].get(f)]
    
    # If there are missing appointment fields, ask for them
    if appointment_missing:
        # Ask for specialty first
        if 'specialty' in appointment_missing:
            state['last_bot_message'] = "Qual especialidade você precisa? (ex: dermatologista, cardiologista, clínico geral)"
            return state
        
        # Then ask for datetime
        if 'preferred_datetime' in appointment_missing:
            state['last_bot_message'] = "Qual seria o melhor dia e horário para você?"
            return state
        
        # Then ask for mode
        if 'mode' in appointment_missing:
            state['last_bot_message'] = "Você prefere atendimento presencial ou online?"
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
    workflow.add_node("check_onboarding", node_check_onboarding)
    workflow.add_node("provide_info", node_provide_clinic_info)
    workflow.add_node("ask_or_confirm", node_ask_missing_or_confirm)
    workflow.add_node("handle_confirmation", node_handle_confirmation_and_save)
    
    # Set entry point
    workflow.set_entry_point("extract")
    
    # Conditional routing after extraction
    def route_after_extract(state: AgentState) -> str:
        # If user is asking for clinic info, go to info node
        if state['intent'] == 'info':
            return "provide_info"
        # Otherwise, check onboarding
        return "check_onboarding"
    
    workflow.add_conditional_edges(
        "extract",
        route_after_extract,
        {
            "provide_info": "provide_info",
            "check_onboarding": "check_onboarding"
        }
    )
    
    # After providing info, end (user can start new conversation for scheduling)
    workflow.add_edge("provide_info", END)
    
    # Normal flow: check_onboarding -> ask_or_confirm
    workflow.add_edge("check_onboarding", "ask_or_confirm")
    
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
            'intent': 'schedule',
            # Onboarding fields
            'patient_id': None,
            'is_onboarded': False,
            'onboarding_step': 'name'
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
