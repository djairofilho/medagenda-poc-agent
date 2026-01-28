# ⚠️ Limitações e Melhorias Futuras

Este documento lista as limitações conhecidas do MedAgenda Bot (POC) e melhorias planejadas para versões futuras.

## 🚧 Limitações Atuais (POC)

### 1. Gerenciamento de Sessões

**Limitação:**
- Sessões armazenadas em memória (Dict global)
- Perdidas ao reiniciar o servidor
- Não escala horizontalmente

**Impacto:**
- Usuário perde contexto se servidor reiniciar
- Impossível usar múltiplas instâncias da API

**Workaround:**
- Aceitar limitação para POC
- Usuário pode recomeçar conversa

**Solução Futura:**
```python
# Fase 2: Usar Redis
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def get_session(session_id: str) -> AgentState:
    data = redis_client.get(f"session:{session_id}")
    if data:
        return json.loads(data)
    return create_new_session()

def save_session(session_id: str, state: AgentState):
    redis_client.setex(
        f"session:{session_id}",
        1800,  # 30 minutos TTL
        json.dumps(state)
    )
```

---

### 2. Extração de Campos (Regex)

**Limitação:**
- Baseada em padrões fixos
- Pode falhar em variações não previstas
- Requer manutenção manual de padrões

**Exemplos de Falha:**

| Input | Problema |
|-------|----------|
| `"João"` | Nome muito curto (< 2 palavras) |
| `"hoje"` | Padrão de data não coberto |
| `"médico"` | Especialidade não específica |
| `"tel: 11987654321"` | Formato não previsto |

**Impacto:**
- Taxa de extração ~85% (bom para POC, mas pode melhorar)
- Casos edge requerem múltiplas tentativas do usuário

**Solução Futura:**
```python
# Fase 3: Usar LLM para extração
def extract_fields_with_llm(text: str) -> dict:
    prompt = f"""
    Extraia os seguintes campos da mensagem:
    - name (nome completo)
    - phone (telefone)
    - specialty (especialidade médica)
    - preferred_datetime (data/hora preferida)
    
    Mensagem: "{text}"
    
    Retorne JSON.
    """
    
    response = llm.invoke(prompt)
    return json.loads(response)
```

---

### 3. Validação de Horários

**Limitação:**
- Aceita qualquer texto para data/hora
- Não valida se horário é válido
- Não verifica slots disponíveis

**Exemplos Aceitos (Inválidos):**
- `"ontem às 14h"` (data passada)
- `"amanhã às 25h"` (hora inválida)
- `"32/13 às 10h"` (data inválida)

**Impacto:**
- Dados inválidos salvos no banco
- Requer validação manual posterior

**Solução Futura:**
```python
from datetime import datetime, timedelta

def validate_datetime(text: str) -> tuple[bool, str | None]:
    """
    Valida e normaliza data/hora.
    
    Returns:
        (is_valid, normalized_datetime)
    """
    # Parsear texto para datetime
    # Validar se é futura
    # Normalizar para ISO 8601
    # Verificar slots disponíveis (integração com sistema)
```

---

### 4. Banco de Dados (SQLite)

**Limitação:**
- Não suporta alta concorrência de escrita
- Arquivo único (dificulta backup/replicação)
- Sem suporte a transações complexas

**Impacto:**
- Máximo ~100 escritas/segundo
- Não adequado para produção em escala

**Solução Futura:**
```sql
-- Fase 2: Migrar para PostgreSQL
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    preferred_datetime TIMESTAMPTZ,  -- Tipo datetime real
    mode VARCHAR(20) DEFAULT 'nao_informado',
    reason TEXT,
    status VARCHAR(20) DEFAULT 'new',
    channel VARCHAR(20) DEFAULT 'unknown',
    
    -- Novos campos
    user_id INTEGER REFERENCES users(id),
    clinic_id INTEGER REFERENCES clinics(id),
    confirmed_datetime TIMESTAMPTZ,
    notes TEXT
);
```

---

### 5. Sem Autenticação

**Limitação:**
- Qualquer um pode acessar a API
- Sem controle de acesso
- Sem auditoria de quem fez o quê

**Impacto:**
- Vulnerável a abuse
- Não adequado para produção

**Solução Futura:**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(
    request: ChatRequest,
    token: str = Depends(security)
):
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401)
    
    # Processar com user_id
```

---

### 6. Sem Rate Limiting

**Limitação:**
- Sem limite de requisições
- Vulnerável a DoS/DDoS
- Sem proteção contra abuse

**Impacto:**
- Servidor pode ser sobrecarregado
- Custos podem explodir (se usar LLM no futuro)

**Solução Futura:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")  # Max 10 req/min
async def chat(request: ChatRequest):
    # ...
```

---

### 7. CORS Aberto

**Limitação:**
- Aceita requisições de qualquer origem
- Configurado para desenvolvimento

**Impacto:**
- Vulnerável a ataques CSRF
- Não adequado para produção

**Solução Futura:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://seudominio.com",
        "https://app.seudominio.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

### 8. Detecção de Escopo (Keywords)

**Limitação:**
- Baseada em lista fixa de keywords
- Pode ter falsos positivos/negativos
- Não entende contexto

**Exemplos de Falha:**

| Input | Problema |
|-------|----------|
| `"Quero marcar para tratar de um problema"` | Falso positivo (palavra "tratar") |
| `"Minha pele está estranha"` | Falso negativo (não detecta pedido de diagnóstico) |

**Solução Futura:**
```python
def detect_out_of_scope_with_llm(text: str) -> bool:
    prompt = f"""
    A seguinte mensagem é um pedido de:
    A) Agendamento de consulta
    B) Diagnóstico/tratamento/orientação médica
    
    Mensagem: "{text}"
    
    Responda apenas A ou B.
    """
    
    response = llm.invoke(prompt)
    return "B" in response
```

---

### 9. Sem Notificações

**Limitação:**
- Não envia confirmação por SMS/Email/WhatsApp
- Usuário não recebe lembrete
- Sem follow-up automático

**Impacto:**
- Taxa de no-show pode ser alta
- Experiência do usuário incompleta

**Solução Futura:**
```python
# Integração com Twilio (SMS/WhatsApp)
from twilio.rest import Client

def send_confirmation(phone: str, appointment_id: int):
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f"✅ Consulta #{appointment_id} agendada!",
        from_='+5511999999999',
        to=phone
    )
```

---

### 10. Sem Dashboard Administrativo

**Limitação:**
- Não há interface para visualizar agendamentos
- Não há ferramentas de gestão
- Apenas API REST

**Impacto:**
- Difícil gerenciar agendamentos
- Requer ferramentas externas

**Solução Futura:**
- Dashboard web (React/Vue)
- Filtros e busca avançada
- Exportação para CSV/Excel
- Estatísticas e relatórios

---

## 🚀 Roadmap de Melhorias

### Fase 1: POC (Atual) ✅

- [x] Fluxo conversacional básico
- [x] Extração de campos via regex
- [x] Persistência em SQLite
- [x] API REST
- [x] Interface Streamlit

### Fase 2: MVP (Próximos 3 meses)

- [ ] Migrar sessões para Redis
- [ ] Validação de data/hora
- [ ] Notificações por SMS/Email
- [ ] Autenticação básica (JWT)
- [ ] Rate limiting
- [ ] Logs estruturados

### Fase 3: Produção (6 meses)

- [ ] Migrar para PostgreSQL
- [ ] Extração com LLM (fallback)
- [ ] Dashboard administrativo
- [ ] Integração WhatsApp Business API
- [ ] Multi-tenancy (múltiplas clínicas)
- [ ] Analytics e relatórios

### Fase 4: Escala (1 ano)

- [ ] Microserviços
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] Cache distribuído (Redis Cluster)
- [ ] Load balancer
- [ ] Monitoramento (Prometheus/Grafana)
- [ ] CI/CD completo

---

## 📊 Comparação: Atual vs Futuro

| Aspecto | POC (Atual) | Produção (Futuro) |
|---------|-------------|-------------------|
| **Sessões** | Memória (Dict) | Redis Cluster |
| **Banco** | SQLite | PostgreSQL |
| **Extração** | Regex | LLM + Regex |
| **Auth** | Nenhuma | JWT + OAuth2 |
| **Rate Limit** | Nenhum | 10 req/min |
| **Notificações** | Nenhuma | SMS + Email + WhatsApp |
| **Validação** | Básica | Completa + Slots |
| **Escala** | 1 instância | N instâncias + LB |
| **Monitoramento** | Logs básicos | Prometheus + Grafana |

---

## 🔍 Métricas de Sucesso

### POC (Atual)

- ✅ Taxa de conclusão > 80%
- ✅ Latência < 100ms
- ✅ Precisão extração > 85%

### Produção (Futuro)

- 🎯 Taxa de conclusão > 95%
- 🎯 Latência < 50ms (p95)
- 🎯 Precisão extração > 98%
- 🎯 Uptime > 99.9%
- 🎯 Taxa de no-show < 10%

---

## 📚 Documentos Relacionados

- **[OVERVIEW.md](./OVERVIEW.md)** - Objetivos do projeto
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura atual
- **[SECURITY.md](./SECURITY.md)** - Restrições de segurança

---

[← Voltar ao Índice](./INDEX.md)
