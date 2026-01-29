# 🎯 Melhorias no Fluxo: Identificação de Intenção Dedicada

## 📊 Diagrama Atualizado

![LangGraph Diagram](../langgraph_diagram.png)

## 🔄 O que Mudou?

### ❌ Antes (Misturado)
```
extract_fields
  ├─ Extração de dados
  └─ Detecção de intent (misturado)
      ↓
  [Routing direto]
```

### ✅ Agora (Separado)
```
extract_fields (APENAS extração)
    ↓
identify_intent (APENAS classificação)
    ↓
  [Routing por intent]
    ├─ info → provide_info
    ├─ urgent → handle_urgent
    ├─ out_of_scope → handle_out_of_scope
    └─ schedule → check_onboarding → ...
```

---

## 🎯 Benefícios da Separação

### 1. **Responsabilidade Única (SRP)**
Cada nó tem uma função clara:
- `extract_fields` → Extrai dados
- `identify_intent` → Classifica intenção
- Handlers específicos → Respondem adequadamente

### 2. **Melhor Rastreabilidade**
```python
[Intent] info (clinic information)
[Intent] urgent (LLM detected)
[Intent] out_of_scope (regex detected)
[Intent] schedule (default)
```

### 3. **Roteamento Mais Claro**
```python
def route_by_intent(state: AgentState) -> str:
    intent = state.get('intent', 'schedule')
    
    if intent == 'info':
        return "provide_info"
    elif intent == 'urgent':
        return "handle_urgent"
    elif intent == 'out_of_scope':
        return "handle_out_of_scope"
    else:  # schedule
        return "check_onboarding"
```

### 4. **Handlers Dedicados**
Cada intent tem seu próprio nó:
- `handle_urgent` → Aviso de segurança
- `handle_out_of_scope` → Redirecionamento
- `provide_info` → Informações da clínica
- `check_onboarding` → Fluxo de agendamento

---

## 🏗️ Arquitetura Atual

### **8 Nós Principais:**

1. **`extract`** - Extração de dados (PydanticAI + Regex)
2. **`identify_intent`** ⭐ NOVO - Classificação de intenção
3. **`provide_info`** - Informações da clínica
4. **`handle_urgent`** ⭐ NOVO - Aviso de urgência
5. **`handle_out_of_scope`** ⭐ NOVO - Redirecionamento
6. **`check_onboarding`** - Verifica cadastro
7. **`ask_or_confirm`** - Coleta dados/confirmação
8. **`handle_confirmation`** - Salva agendamento

### **Fluxo Completo:**

```
__start__
    ↓
extract (extrai dados)
    ↓
identify_intent (classifica)
    ↓
  ┌─────┴─────┬─────────┬──────────┐
  │           │         │          │
info      urgent  out_of_scope  schedule
  │           │         │          │
  ↓           ↓         ↓          ↓
provide   handle    handle     check_
_info     _urgent   _out_of    onboarding
  │           │      _scope        │
  │           │         │          ↓
  │           │         │      ask_or_
  │           │         │      confirm
  │           │         │          │
  │           │         │          ↓
  │           │         │      handle_
  │           │         │      confirmation
  │           │         │          │
  └───────────┴─────────┴──────────┘
              ↓
           __end__
```

---

## 🎭 Detecção de Intenção

### Prioridade de Detecção

**1. Flags LLM (mais confiável)**
```python
if state.get('_llm_out_of_scope', False):
    return 'out_of_scope'

if state.get('_llm_urgent', False):
    return 'urgent'
```

**2. Regex (fallback)**
```python
detected_intent = detect_intent(last_message)

if detected_intent == 'info':
    return 'info'
```

**3. Default**
```python
return 'schedule'
```

### Keywords por Intent

**Info:**
- endereço, onde fica, localização
- horário, funciona, abre, fecha
- serviços, especialidades
- convênio, estacionamento
- acessibilidade, contato

**Urgent:**
- dor no peito, falta de ar
- sangramento, desmaio
- febre alta, convulsão

**Out of Scope:**
- diagnóstico, tratamento
- remédio, medicamento
- o que fazer, como tratar

---

## 📈 Comparação

| Aspecto | Antes | Agora |
|---------|-------|-------|
| **Nós** | 5 | 8 |
| **Separação de Responsabilidades** | ❌ Misturado | ✅ Separado |
| **Rastreabilidade** | ⚠️ Limitada | ✅ Completa |
| **Handlers Dedicados** | ❌ Não | ✅ Sim |
| **Logs Claros** | ⚠️ Genéricos | ✅ Específicos |
| **Manutenibilidade** | ⚠️ Média | ✅ Alta |

---

## 🔍 Exemplo de Execução

### Cenário 1: Pedido de Informação
```
User: "Qual o endereço da clínica?"

extract → identify_intent [Intent] info (clinic information)
       → provide_info → END

Bot: "📍 Endereço: Rua Exemplo, 123..."
```

### Cenário 2: Sintoma Urgente
```
User: "Estou com dor no peito forte"

extract → identify_intent [Intent] urgent (LLM detected)
       → handle_urgent → END

Bot: "Posso ajudar a agendar, mas se urgente procure atendimento imediato."
```

### Cenário 3: Pedido de Diagnóstico
```
User: "O que pode ser essa dor de cabeça?"

extract → identify_intent [Intent] out_of_scope (LLM detected)
       → handle_out_of_scope → END

Bot: "Eu só ajudo a marcar consulta. Você quer agendar com qual especialidade?"
```

### Cenário 4: Agendamento Normal
```
User: "Quero marcar consulta"

extract → identify_intent [Intent] schedule (default)
       → check_onboarding → ask_or_confirm → ...

Bot: "Qual é o seu nome completo?"
```

---

## 🚀 Próximas Melhorias Possíveis

1. **Intent Confidence Score**
   - Adicionar score de confiança (0-1)
   - Pedir confirmação se score < 0.7

2. **Multi-Intent Detection**
   - Detectar múltiplas intenções em uma mensagem
   - Ex: "Qual o endereço? Quero marcar consulta"

3. **Intent History**
   - Manter histórico de intents da sessão
   - Detectar mudanças de contexto

4. **Custom Intents**
   - Cancelamento de consulta
   - Reagendamento
   - Consulta de status

5. **A/B Testing**
   - Testar diferentes estratégias de detecção
   - Métricas de acurácia

---

**Última atualização:** 2026-01-28
**Versão:** 2.0 (Intent Identification)
