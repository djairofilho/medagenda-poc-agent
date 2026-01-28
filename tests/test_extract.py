"""Tests for field extraction logic"""
import pytest

from app.agent.extract import (
    extract_phone,
    extract_mode,
    extract_specialty,
    extract_name,
    extract_datetime,
    detect_intent,
    extract_all_fields,
    get_missing_fields
)


class TestPhoneExtraction:
    """Test phone number extraction."""
    
    def test_phone_with_ddd_and_hyphen(self):
        text = "Meu telefone é 11 98765-4321"
        result = extract_phone(text)
        assert result is not None
        assert '11' in result
        assert '98765' in result
        assert '4321' in result
    
    def test_phone_with_country_code(self):
        text = "Me liga no +55 21 99876-5432"
        result = extract_phone(text)
        assert result is not None
        assert '55' in result or '21' in result
    
    def test_phone_with_parentheses(self):
        text = "WhatsApp (11) 91234-5678"
        result = extract_phone(text)
        assert result is not None
        assert '11' in result
    
    def test_phone_no_spaces(self):
        text = "Telefone: 11987654321"
        result = extract_phone(text)
        assert result is not None
    
    def test_no_phone(self):
        text = "Quero marcar consulta"
        result = extract_phone(text)
        assert result is None


class TestModeExtraction:
    """Test mode (presencial/online) extraction."""
    
    def test_presencial(self):
        assert extract_mode("Quero presencial") == "presencial"
        assert extract_mode("Vou pessoalmente") == "presencial"
        assert extract_mode("Prefiro ir no consultório") == "presencial"
    
    def test_online(self):
        assert extract_mode("Prefiro online") == "online"
        assert extract_mode("Pode ser telemedicina") == "online"
        assert extract_mode("Atendimento virtual") == "online"
        assert extract_mode("Por vídeo") == "online"
    
    def test_no_mode(self):
        assert extract_mode("Quero marcar consulta") is None


class TestSpecialtyExtraction:
    """Test specialty extraction and normalization."""
    
    def test_dermatologist_variations(self):
        assert extract_specialty("Preciso de dermato") == "dermatologista"
        assert extract_specialty("Com dermatologista") == "dermatologista"
        assert extract_specialty("Dermatologia") == "dermatologista"
    
    def test_cardiologist_variations(self):
        assert extract_specialty("Cardio") == "cardiologista"
        assert extract_specialty("Cardiologista") == "cardiologista"
        assert extract_specialty("Cardiologia") == "cardiologista"
    
    def test_general_practitioner(self):
        assert extract_specialty("Clínico geral") == "clínico geral"
        assert extract_specialty("Clinico") == "clínico geral"
    
    def test_no_specialty(self):
        assert extract_specialty("Quero marcar consulta") is None


class TestNameExtraction:
    """Test name extraction."""
    
    def test_me_chamo_pattern(self):
        result = extract_name("Oi, me chamo João Silva")
        assert result == "João Silva"
    
    def test_sou_pattern(self):
        result = extract_name("Sou a Maria Santos")
        assert result == "Maria Santos"
    
    def test_nome_pattern(self):
        result = extract_name("Nome: Pedro Oliveira")
        assert result == "Pedro Oliveira"
    
    def test_no_name(self):
        result = extract_name("Quero marcar consulta")
        assert result is None


class TestDateTimeExtraction:
    """Test date/time extraction."""
    
    def test_amanha_pattern(self):
        result = extract_datetime("Amanhã às 14h")
        assert result is not None
        assert "14" in result or "amanhã" in result
    
    def test_date_with_time(self):
        result = extract_datetime("15/02 às 10h30")
        assert result is not None
    
    def test_weekday(self):
        result = extract_datetime("Segunda às 9h")
        assert result is not None
    
    def test_no_datetime(self):
        result = extract_datetime("Quero marcar consulta")
        assert result is None


class TestIntentDetection:
    """Test intent detection for out-of-scope requests."""
    
    def test_schedule_intent(self):
        assert detect_intent("Quero marcar consulta") == "schedule"
        assert detect_intent("Preciso de dermatologista") == "schedule"
    
    def test_out_of_scope_intent(self):
        assert detect_intent("O que eu tenho?") == "out_of_scope"
        assert detect_intent("Qual o diagnóstico?") == "out_of_scope"
        assert detect_intent("Que remédio devo tomar?") == "out_of_scope"
        assert detect_intent("É grave?") == "out_of_scope"
    
    def test_urgent_intent(self):
        assert detect_intent("Estou com dor no peito") == "urgent"
        assert detect_intent("Falta de ar") == "urgent"
        assert detect_intent("Tive um desmaio") == "urgent"


class TestFieldAggregation:
    """Test full field extraction and missing field detection."""
    
    def test_extract_all_fields_complete(self):
        text = "Me chamo João Silva, telefone 11 98765-4321, quero dermato presencial amanhã às 14h"
        extracted = extract_all_fields(text, {})
        
        assert extracted.get('name') == "João Silva"
        assert extracted.get('phone') is not None
        assert extracted.get('specialty') == "dermatologista"
        assert extracted.get('mode') == "presencial"
        assert extracted.get('preferred_datetime') is not None
    
    def test_get_missing_fields(self):
        extracted = {
            'name': 'João Silva',
            'phone': '11987654321'
        }
        missing = get_missing_fields(extracted)
        
        assert 'specialty' in missing
        assert 'preferred_datetime' in missing
        assert 'mode' in missing
        assert 'name' not in missing
        assert 'phone' not in missing
    
    def test_no_missing_fields(self):
        extracted = {
            'name': 'João Silva',
            'phone': '11987654321',
            'specialty': 'dermatologista',
            'preferred_datetime': 'amanhã às 14h',
            'mode': 'presencial'
        }
        missing = get_missing_fields(extracted)
        
        assert len(missing) == 0
