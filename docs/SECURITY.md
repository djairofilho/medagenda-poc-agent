# 🔐 Segurança - MedAgenda Bot

Este documento detalha as restrições de segurança e escopo implementadas no agente.

## 🎯 Princípio Fundamental

**O MedAgenda Bot NÃO é um assistente médico.**

É apenas um **assistente administrativo** para agendamento de consultas.

## 🚫 Restrições de Escopo

### O que o Bot NÃO faz

❌ **Diagnóstico**
- Não identifica doenças
- Não interpreta sintomas
- Não sugere possíveis condições

❌ **Tratamento**
- Não prescreve medicamentos
- Não recomenda terapias
- Não orienta procedimentos

❌ **Orientação Médica**
- Não responde dúvidas clínicas
- Não avalia gravidade de sintomas
- Não substitui consulta médica

❌ **Triagem Clínica**
- Não prioriza casos por gravidade
- Não avalia urgência médica
- Não direciona para especialidades baseado em sintomas

### O que o Bot FAZ

✅ **Agendamento Administrativo**
- Coleta dados do paciente
- Registra preferências de horário
- Anota especialidade desejada
- Salva pedidos de agendamento

## 🛡️ Barreiras de Segurança

### 1. Detecção de Intent Fora de Escopo

**Keywords Monitoradas:**

```python
OUT_OF_SCOPE_KEYWORDS = [
    # Diagnóstico
    "diagnostico", "diagnóstico", "o que pode ser", "o que é",
    "o que e", "identificar", "descobrir",
    
    # Tratamento
    "tratamento", "como tratar", "cura", "curar",
    "remedio", "remédio", "medicamento", "receita",
    
    # Sintomas
    "estou com", "sinto", "sentindo", "dor em", "dor no", "dor na",
    "sintoma", "doença", "doenca",
    
    # Orientação
    "o que fazer", "é grave", "e grave", "é normal", "e normal",
]
```

**Comportamento:**

```python
if detect_out_of_scope_intent(message):
    return OUT_OF_SCOPE_MESSAGE
```

**Mensagem Padrão:**

```
Eu só ajudo a marcar consulta. 
Não posso dar diagnóstico ou orientação médica.

Você quer agendar com qual especialidade?
```

### 2. Detecção de Urgências

**Keywords de Urgência:**

```python
URGENCY_KEYWORDS = [
    "dor no peito", "dor forte no peito",
    "falta de ar", "dificuldade para respirar",
    "sangramento intenso", "muito sangue",
    "desmaio", "desmaiei",
    "convulsao", "convulsão",
    "perda de consciência", "perda de consciencia",
]
```

**Comportamento:**

```python
if detect_urgency(message):
    return URGENCY_MESSAGE
```

**Mensagem de Urgência:**

```
⚠️ ATENÇÃO

Posso ajudar a agendar uma consulta, mas se você 
considerar que é urgente, procure atendimento 
imediato em:

• Pronto-socorro
• UPA (Unidade de Pronto Atendimento)
• Ligue 192 (SAMU)

Você ainda deseja agendar uma consulta?
```

### 3. Escopo Restrito de Dados

**Campos Coletados:**

✅ **Permitido:**
- Nome completo
- Telefone/WhatsApp
- Especialidade desejada
- Data/hora preferida
- Modo de atendimento (presencial/online)
- Motivo (texto livre, opcional)

❌ **NÃO Coletado:**
- Sintomas detalhados
- Histórico médico
- Medicamentos em uso
- Alergias
- Condições pré-existentes

## 🔒 Implementação Técnica

### Arquivo: `app/agent/extract.py`

```python
def detect_out_of_scope_intent(text: str) -> bool:
    """
    Detecta se a mensagem está fora do escopo de agendamento.
    
    Returns:
        True se detectar intent fora de escopo
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in OUT_OF_SCOPE_KEYWORDS)

def detect_urgency(text: str) -> bool:
    """
    Detecta sintomas de urgência médica.
    
    Returns:
        True se detectar sintomas urgentes
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in URGENCY_KEYWORDS)
```

### Arquivo: `app/agent/graph.py`

```python
def node_ask_missing_or_confirm(state: AgentState) -> AgentState:
    """
    Verifica escopo antes de processar.
    """
    # Prioridade 1: Verificar escopo
    if state.get("out_of_scope"):
        return {
            **state,
            "reply": OUT_OF_SCOPE_MESSAGE,
            "awaiting_confirmation": False,
        }
    
    # Prioridade 2: Verificar urgência
    if detect_urgency(state["current_message"]):
        return {
            **state,
            "reply": URGENCY_MESSAGE,
            "awaiting_confirmation": False,
        }
    
    # Continua com fluxo normal...
```

## 📋 Exemplos de Interações

### Exemplo 1: Tentativa de Diagnóstico

```
Usuário: "Estou com dor no peito, o que pode ser?"

Bot: "Eu só ajudo a marcar consulta. 
     Não posso dar diagnóstico ou orientação médica.
     
     Você quer agendar com qual especialidade?"
```

### Exemplo 2: Pedido de Medicamento

```
Usuário: "Que remédio posso tomar para dor de cabeça?"

Bot: "Eu só ajudo a marcar consulta. 
     Não posso dar diagnóstico ou orientação médica.
     
     Você quer agendar com qual especialidade?"
```

### Exemplo 3: Sintoma de Urgência

```
Usuário: "Estou com dor forte no peito e falta de ar"

Bot: "⚠️ ATENÇÃO
     
     Posso ajudar a agendar uma consulta, mas se você 
     considerar que é urgente, procure atendimento 
     imediato em:
     
     • Pronto-socorro
     • UPA (Unidade de Pronto Atendimento)
     • Ligue 192 (SAMU)
     
     Você ainda deseja agendar uma consulta?"
```

### Exemplo 4: Uso Correto (Agendamento)

```
Usuário: "Quero marcar consulta com cardiologista"

Bot: "Ótimo! Para finalizar o agendamento, preciso de:
     
     1. Qual é o seu nome completo?
     2. Qual é o seu WhatsApp/telefone?
     ..."
```

## 🧪 Testes de Segurança

### Arquivo: `tests/test_security.py`

```python
import pytest
from app.agent.extract import detect_out_of_scope_intent, detect_urgency

def test_detect_out_of_scope():
    # Casos que DEVEM ser detectados
    assert detect_out_of_scope_intent("o que pode ser essa dor?")
    assert detect_out_of_scope_intent("preciso de um diagnóstico")
    assert detect_out_of_scope_intent("que remédio tomar?")
    assert detect_out_of_scope_intent("estou com febre")
    
    # Casos que NÃO devem ser detectados
    assert not detect_out_of_scope_intent("quero marcar consulta")
    assert not detect_out_of_scope_intent("preciso de dermatologista")

def test_detect_urgency():
    # Casos que DEVEM ser detectados
    assert detect_urgency("estou com dor no peito")
    assert detect_urgency("falta de ar")
    assert detect_urgency("sangramento intenso")
    
    # Casos que NÃO devem ser detectados
    assert not detect_urgency("dor leve nas costas")
    assert not detect_urgency("quero marcar consulta")
```

## ⚠️ Limitações Conhecidas

### 1. Detecção Baseada em Keywords

**Problema:**
- Pode não detectar variações não previstas
- Pode ter falsos positivos

**Exemplo de Falso Negativo:**
```
Usuário: "Minha pele está estranha, será que é grave?"
# Pode não ser detectado se "estranha" não estiver nas keywords
```

**Exemplo de Falso Positivo:**
```
Usuário: "Quero marcar para tratar de um problema"
# Pode ser detectado por causa de "tratar"
```

**Mitigação:**
- Expandir lista de keywords continuamente
- Considerar usar LLM para detecção mais robusta (futuro)

### 2. Sem Validação de Especialidade vs Sintoma

**Problema:**
- Bot não valida se a especialidade escolhida é adequada

**Exemplo:**
```
Usuário: "Estou com dor no peito, quero dermatologista"
Bot: [Agenda com dermatologista sem questionar]
```

**Mitigação (Futuro):**
- Adicionar sugestão de especialidade baseada em keywords
- Sempre com disclaimer de que é apenas sugestão

## 🚀 Melhorias Futuras

### Fase 2: Detecção com LLM

```python
def detect_out_of_scope_with_llm(text: str) -> bool:
    """
    Usa LLM para detecção mais robusta de intent.
    """
    prompt = f"""
    Classifique a seguinte mensagem:
    
    Mensagem: "{text}"
    
    A mensagem é:
    A) Pedido de agendamento de consulta
    B) Pedido de diagnóstico/tratamento/orientação médica
    
    Responda apenas A ou B.
    """
    
    response = llm.invoke(prompt)
    return "B" in response
```

### Fase 3: Sugestão de Especialidade

```python
def suggest_specialty(symptoms: str) -> str | None:
    """
    Sugere especialidade baseada em sintomas mencionados.
    
    IMPORTANTE: Sempre com disclaimer!
    """
    # Mapeamento sintoma → especialidade
    # Retorna sugestão com disclaimer
```

## 📝 Avisos Legais (Recomendado)

### Disclaimer na Interface

```
⚠️ AVISO IMPORTANTE

Este é um assistente de AGENDAMENTO apenas.

NÃO fornece:
• Diagnóstico médico
• Orientação de tratamento
• Prescrição de medicamentos
• Avaliação de urgência

Em caso de emergência, ligue 192 (SAMU) ou 
procure o pronto-socorro mais próximo.
```

### Termos de Uso (Futuro)

- Usuário deve aceitar termos antes de usar
- Deixar claro as limitações do bot
- Isenção de responsabilidade médica

## 📚 Documentos Relacionados

- **[OVERVIEW.md](./OVERVIEW.md)** - Objetivos e escopo do projeto
- **[AGENT_FLOW.md](./AGENT_FLOW.md)** - Como a detecção é integrada no fluxo
- **[LIMITATIONS.md](./LIMITATIONS.md)** - Limitações conhecidas

---

[← Voltar ao Índice](./INDEX.md)
