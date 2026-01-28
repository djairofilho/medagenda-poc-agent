# 🤖 Contexto para IA - MedAgenda Bot

Este documento fornece contexto completo e estruturado para assistentes de IA que precisam entender, modificar ou estender o projeto MedAgenda Bot.

## 🎯 Propósito do Projeto

**MedAgenda Bot** é um agente conversacional para agendamento de consultas médicas que:
- Coleta dados do paciente via conversa natural
- Extrai campos automaticamente usando regex (sem LLM)
- Confirma dados antes de salvar
- Registra agendamentos em SQLite

**IMPORTANTE**: O agente NÃO faz diagnóstico, tratamento ou orientação médica.

## 📋 Informações Essenciais

### Tecnologias Principais
- **Python 3.11+**
- **FastAPI** - API REST
- **LangGraph** - Orquestração de fluxo conversacional
- **Pydantic** - Validação de dados
- **SQLite** - Persistência
- **Streamlit** - Interface web

### Estrutura de Arquivos Críticos

```
app/
├── main.py              # FastAPI endpoints + gerenciamento de sessões
├── agent/
│   ├── graph.py        # LangGraph state machine (3 nós)
│   ├── extract.py      # Extração de campos via regex
│   ├── prompts.py      # Templates de mensagens
│   └── tools.py        # Utilitários
├── db/
│   └── sqlite.py       # CRUD operations
└── models/
    └── schemas.py      # Pydantic models
```

## 🔄 Fluxo de Execução

### 1. Request → Response
```
POST /chat
  ↓
Validação (Pydantic)
  ↓
Recuperar/Criar Sessão (Dict em memória)
  ↓
Invocar LangGraph Agent
  ↓
Processar através dos 3 nós
  ↓
Atualizar Sessão
  ↓
Retornar ChatResponse
```

### 2. LangGraph State Machine

**Nó 1: `node_extract_fields`**
- Extrai campos da mensagem usando `extract.py`
- Detecta intents fora de escopo
- Calcula campos faltantes
- Atualiza `state["extracted_fields"]` e `state["missing_fields"]`

**Nó 2: `node_ask_missing_or_confirm`**
- Se `out_of_scope=True`: retorna mensagem de escopo
- Se `missing_fields`: pergunta campos faltantes
- Se todos os campos coletados: gera confirmação e seta `awaiting_confirmation=True`

**Nó 3: `node_handle_confirmation_and_save`**
- Só executa se `awaiting_confirmation=True`
- Se usuário confirma ("sim"): salva no SQLite via `db.sqlite.insert_appointment()`
- Se usuário nega ("não"): permite ajustes, volta ao fluxo

### 3. Extração de Campos (`extract.py`)

**Campos Obrigatórios:**
- `name` - Nome completo
- `phone` - Telefone/WhatsApp
- `specialty` - Especialidade médica
- `preferred_datetime` - Data/hora preferida

**Campos Opcionais:**
- `mode` - presencial | online | nao_informado
- `reason` - Motivo da consulta

**Métodos de Extração:**

```python
# Telefone: Regex para formato BR
r'(?:\+?55\s?)?(?:\(?\d{2}\)?[\s-]?)?\d{4,5}[\s-]?\d{4}'

# Nome: Padrões comuns
r'(?:me chamo|meu nome é|sou o|sou a)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+)+)'

# Especialidade: Mapeamento + normalização
"dermato" → "dermatologista"
"cardio" → "cardiologista"

# Modo: Keywords
"presencial", "online", "telemedicina"

# Data/Hora: Captura texto livre
"amanhã às 14h", "15/02 às 10h", "segunda de manhã"
```

## 🗄️ Schema do Banco de Dados

```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,           -- ISO timestamp
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    specialty TEXT NOT NULL,
    preferred_datetime TEXT NOT NULL,   -- Texto livre
    mode TEXT DEFAULT 'nao_informado',  -- presencial|online|nao_informado
    reason TEXT,                        -- Opcional
    status TEXT DEFAULT 'new',          -- new|confirmed|needs_followup
    channel TEXT DEFAULT 'unknown'      -- web|whatsapp|instagram
);
```

## 🔧 Modificações Comuns

### Adicionar Nova Especialidade

**Arquivo**: `app/agent/extract.py`

```python
SPECIALTY_MAPPING = {
    # ... existentes ...
    "nova_especialidade": "Nome Normalizado",
    "variacao1": "Nome Normalizado",
    "variacao2": "Nome Normalizado",
}
```

### Adicionar Novo Campo

**1. Atualizar Schema SQL** (`app/db/sqlite.py`):
```python
def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            -- ... campos existentes ...
            novo_campo TEXT,
        )
    """)
```

**2. Atualizar Pydantic Model** (`app/models/schemas.py`):
```python
class Appointment(BaseModel):
    # ... campos existentes ...
    novo_campo: str | None = None
```

**3. Adicionar Extração** (`app/agent/extract.py`):
```python
def extract_fields(text: str) -> dict:
    fields = {}
    # ... extrações existentes ...
    
    # Nova extração
    novo_campo_match = re.search(r'padrão_regex', text, re.IGNORECASE)
    if novo_campo_match:
        fields["novo_campo"] = novo_campo_match.group(1)
    
    return fields
```

**4. Atualizar Lista de Campos Obrigatórios** (`app/agent/graph.py`):
```python
REQUIRED_FIELDS = ["name", "phone", "specialty", "preferred_datetime", "novo_campo"]
```

### Modificar Mensagens do Bot

**Arquivo**: `app/agent/prompts.py`

```python
GREETING_MESSAGE = "Sua nova mensagem de saudação"
OUT_OF_SCOPE_MESSAGE = "Sua nova mensagem de escopo"
CONFIRMATION_TEMPLATE = "Seu novo template de confirmação com {placeholders}"
```

### Adicionar Novo Endpoint

**Arquivo**: `app/main.py`

```python
@app.post("/novo-endpoint")
async def novo_endpoint(request: NovoRequest) -> NovoResponse:
    # Implementação
    return NovoResponse(...)
```

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── conftest.py           # Fixtures compartilhadas
├── test_extract.py       # Testes de extração de campos
└── test_agent_flow.py    # Testes de fluxo completo
```

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Testes específicos
pytest tests/test_extract.py -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

### Adicionar Novo Teste

```python
# tests/test_extract.py
def test_nova_extracao():
    from app.agent.extract import extract_fields
    
    text = "texto de teste"
    fields = extract_fields(text)
    
    assert fields["novo_campo"] == "valor_esperado"
```

## 🔒 Restrições de Segurança

### Detecção de Escopo

**Arquivo**: `app/agent/extract.py`

```python
OUT_OF_SCOPE_KEYWORDS = [
    "diagnostico", "tratamento", "remedio", "medicamento",
    "o que pode ser", "estou com", "dor em", "sintoma"
]

URGENCY_KEYWORDS = [
    "dor no peito", "falta de ar", "sangramento",
    "desmaio", "convulsao"
]
```

**Comportamento**:
- Se detectar keyword de escopo: retorna mensagem padrão de redirecionamento
- Se detectar urgência: alerta para buscar atendimento imediato

## 📊 Estado da Sessão

```python
class AgentState(TypedDict):
    messages: list[str]              # Histórico completo
    current_message: str             # Mensagem atual
    extracted_fields: dict           # Campos já extraídos
    missing_fields: list[str]        # Campos ainda faltantes
    awaiting_confirmation: bool      # Flag de confirmação
    reply: str                       # Resposta gerada
    out_of_scope: bool              # Flag de escopo
```

**Gerenciamento**:
- Sessões armazenadas em `Dict[str, AgentState]` em memória
- Timeout: 30 minutos de inatividade
- Limpeza automática de sessões expiradas

## 🚀 Comandos Úteis

### Desenvolvimento

```bash
# Ativar ambiente virtual
.\\venv\\Scripts\\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar API
uvicorn app.main:app --reload --port 8000

# Rodar Streamlit
streamlit run streamlit_app.py

# Testes
pytest tests/ -v
```

### Debug

```bash
# Ver logs detalhados
uvicorn app.main:app --reload --log-level debug

# Inspecionar banco
sqlite3 medagenda.db "SELECT * FROM appointments;"

# Limpar banco
rm medagenda.db
```

## 🎯 Casos de Uso Comuns

### 1. Agendamento Completo em Uma Mensagem

```
Input: "Me chamo João Silva, telefone 11 98765-4321, 
        quero dermatologista presencial amanhã às 14h"

Fluxo:
1. Extrai todos os campos
2. Gera confirmação
3. Usuário confirma
4. Salva no banco
```

### 2. Agendamento Gradual

```
Input: "Quero marcar consulta"
→ Bot: "Qual especialidade?"

Input: "Cardiologista"
→ Bot: "Qual seu nome?"

Input: "João Silva"
→ Bot: "Qual seu telefone?"

[... continua até coletar tudo]
```

### 3. Intent Fora de Escopo

```
Input: "Estou com dor no peito, o que pode ser?"
→ Bot: "Eu só ajudo a marcar consulta. 
       Você quer agendar com qual especialidade?"
```

## 📝 Convenções de Código

### Estilo
- **PEP 8** para Python
- **Type hints** em todas as funções
- **Docstrings** para funções públicas

### Nomenclatura
- **snake_case** para funções e variáveis
- **PascalCase** para classes
- **UPPER_CASE** para constantes

### Imports
```python
# Padrão
from typing import TypedDict
import re

# Terceiros
from fastapi import FastAPI
from pydantic import BaseModel

# Locais
from app.agent.extract import extract_fields
from app.db.sqlite import insert_appointment
```

## 🔍 Debugging Tips

### Verificar Estado da Sessão

```python
# Em app/main.py, adicione log
print(f"Session state: {sessions.get(session_id)}")
```

### Testar Extração Isoladamente

```python
from app.agent.extract import extract_fields

text = "sua mensagem de teste"
fields = extract_fields(text)
print(fields)
```

### Verificar Fluxo do Grafo

```python
# Em app/agent/graph.py, adicione logs em cada nó
print(f"[Node Extract] State: {state}")
```

## 📚 Recursos Adicionais

- **[OVERVIEW.md](./OVERVIEW.md)** - Visão geral do projeto
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura detalhada
- **[AGENT_FLOW.md](./AGENT_FLOW.md)** - Fluxo do LangGraph
- **[API.md](./API.md)** - Documentação da API

## ⚠️ Limitações Conhecidas

1. **Sessões em Memória**: Não persistem entre restarts
2. **Extração Simples**: Regex pode falhar em casos complexos
3. **Sem Validação de Horários**: Aceita qualquer texto para data/hora
4. **Sem Rate Limiting**: Vulnerável a abuse
5. **CORS Aberto**: Aceita todas as origens

## 🚀 Próximos Passos Sugeridos

Para melhorar o projeto:

1. **Migrar sessões para Redis**
2. **Adicionar validação de slots de horário**
3. **Implementar rate limiting**
4. **Usar LLM para extração mais robusta**
5. **Adicionar autenticação**
6. **Integrar com WhatsApp Business API**

---

[← Voltar ao Índice](./INDEX.md)
