"""Tests for agent conversation flow"""
import pytest

from app.agent.graph import (
    process_message,
    reset_session,
    get_or_create_session
)
from app.agent.prompts import GREETING, OUT_OF_SCOPE


class TestAgentFlow:
    """Test complete agent conversation flows."""
    
    def test_initial_greeting(self, clean_sessions):
        """Test that initial session returns greeting."""
        session_id = "test_greeting"
        state = get_or_create_session(session_id)
        
        assert state['last_bot_message'] == GREETING
        assert len(state['messages']) == 0
    
    def test_out_of_scope_handling(self, clean_sessions):
        """Test that medical advice requests are rejected."""
        session_id = "test_out_of_scope"
        
        # Ask for diagnosis
        reply = process_message(session_id, "O que eu tenho? Estou com dor de cabeça")
        
        assert OUT_OF_SCOPE in reply
        assert "marcar consulta" in reply.lower()
    
    def test_missing_fields_flow(self, clean_sessions):
        """Test that agent asks for missing fields."""
        session_id = "test_missing"
        
        # Start with minimal info
        reply = process_message(session_id, "Quero marcar consulta")
        
        # Should ask for fields
        assert any(word in reply.lower() for word in ['especialidade', 'nome', 'telefone'])
    
    def test_complete_flow_with_confirmation(self, clean_sessions):
        """Test complete flow: provide all info -> confirm -> save."""
        session_id = "test_complete"
        
        # Provide all information at once
        reply1 = process_message(
            session_id,
            "Me chamo João Silva, telefone 11 98765-4321, quero dermatologista presencial amanhã às 14h"
        )
        
        # Should ask for confirmation
        assert "confirmar" in reply1.lower() or "está tudo certo" in reply1.lower()
        
        # Get state to check
        state = get_or_create_session(session_id)
        assert state['awaiting_confirmation'] is True
        
        # Confirm
        reply2 = process_message(session_id, "sim")
        
        # Should have appointment ID
        assert "agendada" in reply2.lower() or "sucesso" in reply2.lower()
        
        state = get_or_create_session(session_id)
        assert state['appointment_id'] is not None
    
    def test_confirmation_rejection(self, clean_sessions):
        """Test that user can reject confirmation and adjust."""
        session_id = "test_reject"
        
        # Provide all information
        process_message(
            session_id,
            "Me chamo Maria Santos, telefone 21 99876-5432, quero cardiologista online segunda às 10h"
        )
        
        # Reject confirmation
        reply = process_message(session_id, "não")
        
        # Should ask what to adjust
        assert "ajustar" in reply.lower()
        
        state = get_or_create_session(session_id)
        assert state['awaiting_confirmation'] is False
        assert state['appointment_id'] is None
    
    def test_incremental_field_collection(self, clean_sessions):
        """Test collecting fields incrementally."""
        session_id = "test_incremental"
        
        # Start
        reply1 = process_message(session_id, "Quero marcar consulta")
        
        # Provide specialty
        reply2 = process_message(session_id, "Dermatologista")
        
        # Should still ask for more fields
        state = get_or_create_session(session_id)
        assert state['extracted'].get('specialty') == 'dermatologista'
        assert len(state['missing_fields']) > 0
        
        # Provide name
        reply3 = process_message(session_id, "Me chamo Pedro Oliveira")
        
        state = get_or_create_session(session_id)
        assert state['extracted'].get('name') == 'Pedro Oliveira'
    
    def test_session_reset(self, clean_sessions):
        """Test that session reset clears state."""
        session_id = "test_reset"
        
        # Create session with some data
        process_message(session_id, "Me chamo João Silva")
        
        state = get_or_create_session(session_id)
        assert len(state['messages']) > 0
        
        # Reset
        reset_session(session_id)
        
        # Should be fresh
        new_state = get_or_create_session(session_id)
        assert len(new_state['messages']) == 0
        assert new_state['last_bot_message'] == GREETING


class TestToolFunctions:
    """Test utility tool functions."""
    
    def test_affirmative_detection(self):
        from app.agent.tools import is_affirmative
        
        assert is_affirmative("sim") is True
        assert is_affirmative("s") is True
        assert is_affirmative("confirmar") is True
        assert is_affirmative("ok") is True
        assert is_affirmative("não") is False
    
    def test_negative_detection(self):
        from app.agent.tools import is_negative
        
        assert is_negative("não") is True
        assert is_negative("nao") is True
        assert is_negative("n") is True
        assert is_negative("sim") is False
