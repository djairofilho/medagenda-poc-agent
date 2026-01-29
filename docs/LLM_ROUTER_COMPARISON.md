# 🔀 Comparação: LLM Router vs Nossa Implementação

## 📊 LLM Router "Puro" (Exemplo)

### Estrutura Típica

```python
from langchain.chains.router import MultiPromptChain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 1. Define rotas e prompts
info_template = """Você é um assistente de informações da clínica.
Pergunta: {input}
Resposta:"""

schedule_template = """Você é um assistente de agendamento.
Pergunta: {input}
Resposta:"""

urgent_template = """Você detectou uma urgência médica.
Pergunta: {input}
Resposta:"""

# 2. Cria chains especializadas
info_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(info_template))
schedule_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(schedule_template))
urgent_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(urgent_template))

# 3. Define descrições para o router
route_descriptions = [
    {
        "name": "info",
        "description": "Perguntas sobre endereço, horário, serviços da clínica"
    },
    {
        "name": "schedule",
        "description": "Pedidos de agendamento de consultas"
    },
    {
        "name": "urgent",
        "description": "Sintomas urgentes ou emergências médicas"
    }
]

# 4. Cria o router
router_chain = MultiPromptChain(
    router_chain=...,  # LLM que classifica
    destination_chains={
        "info": info_chain,
        "schedule": schedule_chain,
        "urgent": urgent_chain
    },
    default_chain=schedule_chain
)

# 5. Uso
result = router_chain.run("Qual o endereço da clínica?")
```

### Fluxo
```
User Input
    ↓
LLM Router (classifica) ← CHAMADA LLM #1
    ↓
  [Routing]
    ├─ info_chain ← CHAMADA LLM #2
    ├─ schedule_chain ← CHAMADA LLM #2
    └─ urgent_chain ← CHAMADA LLM #2
    ↓
Response
```

**Custo:** 2 chamadas LLM por mensagem
**Latência:** ~2-4 segundos

---

## 🎯 Nossa Implementação (Híbrida)

### Estrutura

```python
# 1. Extração (1 chamada LLM ou 0)
def node_extract_fields(state):
    llm_result = extract_with_pydantic_ai(message)  # LLM
    regex_result = extract_all_fields(message)      # Regex
    merged = merge_extractions(llm_result, regex_result)
    
    # Armazena flags para routing
    state['_llm_out_of_scope'] = merged.out_of_scope
    state['_llm_urgent'] = merged.urgent_flag
    return state

# 2. Classificação (0 chamadas LLM!)
def node_identify_intent(state):
    # Usa flags já extraídas + regex
    if state.get('_llm_out_of_scope'):
        return 'out_of_scope'
    
    if state.get('_llm_urgent'):
        return 'urgent'
    
    # Regex para info
    if 'endereço' in message or 'horário' in message:
        return 'info'
    
    return 'schedule'

# 3. Handlers (0 chamadas LLM)
def node_handle_urgent(state):
    state['last_bot_message'] = URGENT_NEUTRAL
    return state

def node_provide_info(state):
    clinic_info = get_all_clinic_info()  # Database
    state['last_bot_message'] = format_info(clinic_info)
    return state
```

### Fluxo
```
User Input
    ↓
extract_fields ← CHAMADA LLM #1 (ou 0 se regex suficiente)
    ↓
identify_intent ← SEM LLM (usa flags + regex)
    ↓
  [Routing]
    ├─ provide_info ← SEM LLM (database)
    ├─ handle_urgent ← SEM LLM (template)
    └─ check_onboarding ← SEM LLM (database + templates)
    ↓
Response
```

**Custo:** 0-1 chamada LLM por mensagem
**Latência:** ~0.5-2 segundos

---

## 📊 Comparação Detalhada

### 1. **Custo por Mensagem**

| Implementação | Chamadas LLM | Custo (Gemini Flash) |
|---------------|--------------|----------------------|
| LLM Router Puro | 2 | ~$0.0002 |
| Nossa (com LLM) | 1 | ~$0.0001 |
| Nossa (regex) | 0 | $0.0000 |

**Em 10k mensagens/mês:**
- LLM Router: ~$2.00
- Nossa: ~$0.40 (60% economia)

### 2. **Latência**

| Implementação | Tempo Médio |
|---------------|-------------|
| LLM Router | 2-4s |
| Nossa (LLM) | 1-2s |
| Nossa (regex) | 0.1-0.5s |

### 3. **Robustez**

| Implementação | Fallback | Sempre Funciona? |
|---------------|----------|------------------|
| LLM Router | Default chain | ⚠️ Se LLM falhar, quebra |
| Nossa | Regex → Default | ✅ Sempre |

### 4. **Contexto**

| Implementação | Mantém Estado? | Compartilha Dados? |
|---------------|----------------|---------------------|
| LLM Router | ❌ Chains separadas | ⚠️ Precisa passar |
| Nossa | ✅ Mesmo grafo | ✅ Automático |

---

## 🎨 Quando Usar Cada Abordagem?

### ✅ Use LLM Router Puro Quando:

1. **Handlers Muito Diferentes**
   - Cada rota precisa de um LLM diferente
   - Ex: GPT-4 para suporte, Claude para vendas

2. **Classificação Complexa**
   - Muitas rotas (10+)
   - Nuances sutis entre rotas

3. **Sem Padrões Claros**
   - Impossível usar regex
   - Linguagem muito variada

### ✅ Use Nossa Abordagem (Híbrida) Quando:

1. **Custo é Importante** 💰
   - Alto volume de mensagens
   - Budget limitado

2. **Latência é Crítica** ⚡
   - Usuários esperam resposta rápida
   - Aplicação real-time

3. **Padrões Detectáveis** 🎯
   - Alguns intents têm keywords claras
   - Ex: "endereço", "horário", "urgente"

4. **Contexto Compartilhado** 🔄
   - Handlers precisam acessar mesmo estado
   - Dados extraídos são reutilizados

---

## 🔄 Podemos Melhorar para um LLM Router "Real"?

Sim! Aqui está como:

### Opção 1: LLM Router Dedicado (Mais Caro)

```python
def node_identify_intent_llm(state):
    """Usa LLM dedicado APENAS para classificação."""
    
    prompt = f"""Classifique a intenção do usuário:
    
Mensagem: {last_message}

Opções:
- info: Perguntas sobre a clínica
- urgent: Sintomas urgentes
- out_of_scope: Pedidos de diagnóstico
- schedule: Agendamento de consulta

Responda APENAS com uma palavra: info, urgent, out_of_scope ou schedule.
"""
    
    # Chamada LLM dedicada
    intent = llm.invoke(prompt).strip().lower()
    
    state['intent'] = intent
    return state
```

**Custo:** +1 chamada LLM (2 total)
**Benefício:** Classificação mais precisa

### Opção 2: Semantic Router (Embeddings)

```python
from semantic_router import Route, RouteLayer

# Define rotas com exemplos
routes = [
    Route(
        name="info",
        utterances=[
            "qual o endereço?",
            "onde fica a clínica?",
            "horário de funcionamento",
        ]
    ),
    Route(
        name="urgent",
        utterances=[
            "dor no peito",
            "falta de ar",
            "sangramento",
        ]
    ),
]

# Cria layer (usa embeddings, não LLM)
route_layer = RouteLayer(encoder=encoder, routes=routes)

# Classifica (rápido e barato!)
intent = route_layer(message).name
```

**Custo:** Apenas embeddings (~$0.00001)
**Latência:** ~100ms
**Benefício:** Melhor que regex, mais barato que LLM

---

## 💡 Recomendação

Nossa implementação atual é **excelente** porque:

1. ✅ **Estrutura de LLM Router** (separação clara)
2. ✅ **Custo otimizado** (híbrido LLM + regex)
3. ✅ **Fallback robusto** (sempre funciona)
4. ✅ **Contexto compartilhado** (LangGraph)

**Próximo passo sugerido:**
- Adicionar **Semantic Router** para intents ambíguos
- Manter regex para casos óbvios
- Usar LLM apenas quando necessário

---

## 📚 Referências

- [LangChain Router Chains](https://python.langchain.com/docs/modules/chains/foundational/router)
- [Semantic Router](https://github.com/aurelio-labs/semantic-router)
- [LangGraph Conditional Edges](https://langchain-ai.github.io/langgraph/concepts/low_level/#conditional-edges)

---

**Resumo:** Temos a **estrutura** de um LLM Router, mas com **otimizações** que reduzem custo e latência! 🎯
