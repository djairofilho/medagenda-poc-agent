# 📡 API - MedAgenda Bot

Este documento detalha todos os endpoints REST da API FastAPI implementada em `app/main.py`.

## 🌐 Base URL

```
http://localhost:8000
```

## 📚 Documentação Interativa

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Endpoints

### 1. POST `/chat`

Processa uma mensagem do usuário através do agente conversacional.

#### Request

```http
POST /chat HTTP/1.1
Content-Type: application/json

{
  "session_id": "user123",
  "message": "Quero marcar consulta com dermatologista",
  "channel": "web"
}
```

#### Request Schema

```python
class ChatRequest(BaseModel):
    session_id: str          # ID único da sessão (obrigatório)
    message: str             # Mensagem do usuário (obrigatório)
    channel: str = "unknown" # Canal de origem (opcional)
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "user123",
  "reply": "Ótimo! Para finalizar o agendamento, preciso de algumas informações:\n\n1. Qual é o seu nome completo?\n2. Qual é o seu WhatsApp/telefone?\n..."
}
```

#### Response Schema

```python
class ChatResponse(BaseModel):
    session_id: str  # ID da sessão
    reply: str       # Resposta do agente
```

#### Exemplos

**Exemplo 1: Primeira mensagem**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test1",
    "message": "Oi",
    "channel": "web"
  }'
```

**Exemplo 2: Fornecer todas as informações**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test1",
    "message": "Me chamo João Silva, telefone 11 98765-4321, quero dermatologista presencial amanhã às 14h",
    "channel": "web"
  }'
```

**Exemplo 3: Confirmar agendamento**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test1",
    "message": "sim",
    "channel": "web"
  }'
```

---

### 2. GET `/appointments`

Lista agendamentos com paginação.

#### Request

```http
GET /appointments?limit=10&offset=0 HTTP/1.1
```

#### Query Parameters

| Parâmetro | Tipo | Default | Descrição |
|-----------|------|---------|-----------|
| `limit` | int | 10 | Número máximo de resultados (max: 100) |
| `offset` | int | 0 | Número de registros para pular |

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "total": 5,
  "appointments": [
    {
      "id": 1,
      "created_at": "2026-01-28T14:30:00.123456+00:00",
      "name": "João Silva",
      "phone": "11987654321",
      "specialty": "dermatologista",
      "preferred_datetime": "amanhã às 14h",
      "mode": "presencial",
      "reason": null,
      "status": "confirmed",
      "channel": "web"
    },
    {
      "id": 2,
      "created_at": "2026-01-28T15:00:00.123456+00:00",
      "name": "Maria Santos",
      "phone": "11912345678",
      "specialty": "cardiologista",
      "preferred_datetime": "15/02 às 10h",
      "mode": "online",
      "reason": "consulta de rotina",
      "status": "new",
      "channel": "web"
    }
  ]
}
```

#### Response Schema

```python
class AppointmentListResponse(BaseModel):
    total: int                    # Total de agendamentos no banco
    appointments: list[Appointment]  # Lista de agendamentos
```

#### Exemplos

**Exemplo 1: Listar primeiros 10**

```bash
curl http://localhost:8000/appointments
```

**Exemplo 2: Listar com paginação**

```bash
curl http://localhost:8000/appointments?limit=5&offset=10
```

**Exemplo 3: Listar todos (max 100)**

```bash
curl http://localhost:8000/appointments?limit=100
```

---

### 3. GET `/appointments/{id}`

Busca um agendamento específico por ID.

#### Request

```http
GET /appointments/1 HTTP/1.1
```

#### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id` | int | ID do agendamento |

#### Response (Sucesso)

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 1,
  "created_at": "2026-01-28T14:30:00.123456+00:00",
  "name": "João Silva",
  "phone": "11987654321",
  "specialty": "dermatologista",
  "preferred_datetime": "amanhã às 14h",
  "mode": "presencial",
  "reason": null,
  "status": "confirmed",
  "channel": "web"
}
```

#### Response (Não Encontrado)

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Appointment not found"
}
```

#### Response Schema

```python
class Appointment(BaseModel):
    id: int
    created_at: str
    name: str
    phone: str
    specialty: str
    preferred_datetime: str
    mode: str
    reason: str | None
    status: str
    channel: str
```

#### Exemplos

**Exemplo 1: Buscar agendamento existente**

```bash
curl http://localhost:8000/appointments/1
```

**Exemplo 2: Buscar agendamento inexistente**

```bash
curl http://localhost:8000/appointments/999
# Retorna 404
```

---

### 4. POST `/sessions/{session_id}/reset`

Reseta/limpa uma sessão específica.

#### Request

```http
POST /sessions/test1/reset HTTP/1.1
```

#### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `session_id` | str | ID da sessão para resetar |

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "test1",
  "message": "Session reset successfully"
}
```

#### Response Schema

```python
class SessionResetResponse(BaseModel):
    session_id: str
    message: str
```

#### Exemplos

**Exemplo 1: Resetar sessão existente**

```bash
curl -X POST http://localhost:8000/sessions/test1/reset
```

**Exemplo 2: Resetar sessão inexistente (também funciona)**

```bash
curl -X POST http://localhost:8000/sessions/nova_sessao/reset
```

---

## 🔒 CORS

A API está configurada para aceitar requisições de **todas as origens** (desenvolvimento):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **Em produção**, restrinja as origens:

```python
allow_origins=["https://seudominio.com"]
```

## 📊 Códigos de Status HTTP

| Código | Significado | Quando Ocorre |
|--------|-------------|---------------|
| `200 OK` | Sucesso | Request processado com sucesso |
| `404 Not Found` | Não encontrado | Agendamento não existe |
| `422 Unprocessable Entity` | Validação falhou | Dados inválidos no request |
| `500 Internal Server Error` | Erro interno | Erro inesperado no servidor |

## 🧪 Testes com cURL

### Fluxo Completo de Agendamento

```bash
# 1. Iniciar conversa
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Oi",
    "channel": "web"
  }'

# 2. Fornecer informações
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "Me chamo João Silva, telefone 11 98765-4321, quero dermatologista presencial amanhã às 14h",
    "channel": "web"
  }'

# 3. Confirmar
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo",
    "message": "sim",
    "channel": "web"
  }'

# 4. Verificar agendamento criado
curl http://localhost:8000/appointments/1

# 5. Listar todos os agendamentos
curl http://localhost:8000/appointments

# 6. Resetar sessão
curl -X POST http://localhost:8000/sessions/demo/reset
```

## 🧪 Testes com PowerShell

```powershell
# POST /chat
Invoke-RestMethod -Uri "http://localhost:8000/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"session_id":"test1","message":"Oi","channel":"web"}'

# GET /appointments
Invoke-RestMethod -Uri "http://localhost:8000/appointments?limit=5"

# GET /appointments/{id}
Invoke-RestMethod -Uri "http://localhost:8000/appointments/1"

# POST /sessions/{id}/reset
Invoke-RestMethod -Uri "http://localhost:8000/sessions/test1/reset" `
  -Method POST
```

## 🧪 Testes com Python

```python
import requests

BASE_URL = "http://localhost:8000"

# POST /chat
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "session_id": "test1",
        "message": "Oi",
        "channel": "web"
    }
)
print(response.json())

# GET /appointments
response = requests.get(f"{BASE_URL}/appointments?limit=5")
print(response.json())

# GET /appointments/{id}
response = requests.get(f"{BASE_URL}/appointments/1")
print(response.json())

# POST /sessions/{id}/reset
response = requests.post(f"{BASE_URL}/sessions/test1/reset")
print(response.json())
```

## 📝 Validação de Dados

### ChatRequest

```python
class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=5000)
    channel: str = Field(default="unknown")
```

**Erros de Validação:**

```bash
# session_id vazio
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"","message":"Oi"}'
# Retorna 422

# message muito longa (> 5000 caracteres)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"'$(python -c 'print("a"*5001)')'"}'
# Retorna 422
```

## 🔍 Logs e Debug

### Habilitar Logs Detalhados

```bash
uvicorn app.main:app --reload --log-level debug
```

### Exemplo de Log

```
INFO:     127.0.0.1:54321 - "POST /chat HTTP/1.1" 200 OK
DEBUG:    Session test1 state: {'messages': ['Oi'], 'current_message': 'Oi', ...}
INFO:     Agent processed message in 45ms
```

## 📊 Rate Limiting (Futuro)

**Não implementado no POC**, mas recomendado para produção:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("10/minute")  # Max 10 requests por minuto
async def chat(request: ChatRequest):
    # ...
```

## 🔐 Autenticação (Futuro)

**Não implementado no POC**, mas recomendado para produção:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(
    request: ChatRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validar token
    if not validate_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    # ...
```

## 📚 Documentos Relacionados

- **[AGENT_FLOW.md](./AGENT_FLOW.md)** - Como o endpoint /chat processa mensagens
- **[DATABASE.md](./DATABASE.md)** - Como os dados são armazenados
- **[USAGE.md](./USAGE.md)** - Exemplos práticos de uso

---

[← Voltar ao Índice](./INDEX.md)
