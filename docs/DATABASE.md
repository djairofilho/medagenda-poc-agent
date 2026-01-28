# 🗄️ Banco de Dados - MedAgenda Bot

Este documento detalha o esquema do banco de dados SQLite e as operações implementadas em `app/db/sqlite.py`.

## 🎯 Visão Geral

O MedAgenda usa **SQLite** como banco de dados para:
- ✅ Zero configuração e dependências
- ✅ Arquivo único portável (`medagenda.db`)
- ✅ Suficiente para POC e testes
- ✅ Fácil migração para PostgreSQL no futuro

## 📊 Schema do Banco

### Tabela: `appointments`

```sql
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    specialty TEXT NOT NULL,
    preferred_datetime TEXT NOT NULL,
    mode TEXT DEFAULT 'nao_informado',
    reason TEXT,
    status TEXT DEFAULT 'new',
    channel TEXT DEFAULT 'unknown'
);
```

### Índices

```sql
-- Índice para busca por telefone
CREATE INDEX IF NOT EXISTS idx_appointments_phone 
ON appointments(phone);

-- Índice para ordenação por data de criação
CREATE INDEX IF NOT EXISTS idx_appointments_created_at 
ON appointments(created_at);
```

## 📋 Descrição dos Campos

| Campo | Tipo | Nullable | Default | Descrição |
|-------|------|----------|---------|-----------|
| `id` | INTEGER | NOT NULL | AUTO | ID único do agendamento |
| `created_at` | TEXT | NOT NULL | - | Timestamp ISO 8601 de criação |
| `name` | TEXT | NOT NULL | - | Nome completo do paciente |
| `phone` | TEXT | NOT NULL | - | Telefone/WhatsApp (apenas números) |
| `specialty` | TEXT | NOT NULL | - | Especialidade médica normalizada |
| `preferred_datetime` | TEXT | NOT NULL | - | Data/hora preferida (texto livre) |
| `mode` | TEXT | NULL | `'nao_informado'` | Modo: `presencial`, `online`, `nao_informado` |
| `reason` | TEXT | NULL | NULL | Motivo da consulta (opcional) |
| `status` | TEXT | NULL | `'new'` | Status: `new`, `confirmed`, `needs_followup` |
| `channel` | TEXT | NULL | `'unknown'` | Canal: `web`, `whatsapp`, `instagram`, `unknown` |

## 🔧 Operações CRUD

### 1. Inicializar Banco

```python
def init_db(db_path: str = "medagenda.db") -> None:
    """
    Inicializa o banco de dados criando tabelas e índices.
    
    Args:
        db_path: Caminho para o arquivo do banco
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            specialty TEXT NOT NULL,
            preferred_datetime TEXT NOT NULL,
            mode TEXT DEFAULT 'nao_informado',
            reason TEXT,
            status TEXT DEFAULT 'new',
            channel TEXT DEFAULT 'unknown'
        )
    """)
    
    # Criar índices
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_phone 
        ON appointments(phone)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_created_at 
        ON appointments(created_at)
    """)
    
    conn.commit()
    conn.close()
```

### 2. Inserir Agendamento

```python
def insert_appointment(data: dict, db_path: str = "medagenda.db") -> int:
    """
    Insere um novo agendamento no banco.
    
    Args:
        data: Dicionário com os dados do agendamento
        db_path: Caminho para o arquivo do banco
        
    Returns:
        ID do agendamento criado
        
    Example:
        >>> data = {
        ...     "name": "João Silva",
        ...     "phone": "11987654321",
        ...     "specialty": "dermatologista",
        ...     "preferred_datetime": "amanhã às 14h",
        ...     "mode": "presencial",
        ...     "reason": "consulta de rotina",
        ...     "channel": "web"
        ... }
        >>> appointment_id = insert_appointment(data)
        >>> print(appointment_id)
        1
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Timestamp atual em ISO 8601
    created_at = datetime.now(timezone.utc).isoformat()
    
    cursor.execute("""
        INSERT INTO appointments (
            created_at, name, phone, specialty, preferred_datetime,
            mode, reason, status, channel
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        created_at,
        data["name"],
        data["phone"],
        data["specialty"],
        data["preferred_datetime"],
        data.get("mode", "nao_informado"),
        data.get("reason"),
        data.get("status", "new"),
        data.get("channel", "unknown"),
    ))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return appointment_id
```

### 3. Buscar Agendamento por ID

```python
def get_appointment_by_id(appointment_id: int, db_path: str = "medagenda.db") -> dict | None:
    """
    Busca um agendamento específico por ID.
    
    Args:
        appointment_id: ID do agendamento
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Dicionário com os dados do agendamento ou None se não encontrado
        
    Example:
        >>> appointment = get_appointment_by_id(1)
        >>> print(appointment["name"])
        João Silva
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM appointments WHERE id = ?
    """, (appointment_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None
```

### 4. Listar Agendamentos (Paginado)

```python
def list_appointments(
    limit: int = 10, 
    offset: int = 0, 
    db_path: str = "medagenda.db"
) -> list[dict]:
    """
    Lista agendamentos com paginação.
    
    Args:
        limit: Número máximo de resultados (max: 100)
        offset: Número de registros para pular
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Lista de dicionários com os agendamentos
        
    Example:
        >>> appointments = list_appointments(limit=5, offset=0)
        >>> print(len(appointments))
        5
    """
    # Limitar máximo de 100 por request
    limit = min(limit, 100)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM appointments 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
```

### 5. Contar Agendamentos

```python
def count_appointments(db_path: str = "medagenda.db") -> int:
    """
    Conta o total de agendamentos no banco.
    
    Args:
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Número total de agendamentos
        
    Example:
        >>> total = count_appointments()
        >>> print(total)
        42
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count
```

### 6. Buscar por Telefone

```python
def get_appointments_by_phone(phone: str, db_path: str = "medagenda.db") -> list[dict]:
    """
    Busca todos os agendamentos de um telefone.
    
    Args:
        phone: Telefone para buscar
        db_path: Caminho para o arquivo do banco
        
    Returns:
        Lista de agendamentos do telefone
        
    Example:
        >>> appointments = get_appointments_by_phone("11987654321")
        >>> print(len(appointments))
        3
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM appointments 
        WHERE phone = ? 
        ORDER BY created_at DESC
    """, (phone,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
```

## 📊 Exemplo de Dados

### Registro Completo

```json
{
  "id": 1,
  "created_at": "2026-01-28T14:30:00.123456+00:00",
  "name": "João Silva",
  "phone": "11987654321",
  "specialty": "dermatologista",
  "preferred_datetime": "amanhã às 14h",
  "mode": "presencial",
  "reason": "consulta de rotina",
  "status": "confirmed",
  "channel": "web"
}
```

### Registro Mínimo

```json
{
  "id": 2,
  "created_at": "2026-01-28T15:00:00.123456+00:00",
  "name": "Maria Santos",
  "phone": "11912345678",
  "specialty": "cardiologista",
  "preferred_datetime": "15/02 às 10h",
  "mode": "nao_informado",
  "reason": null,
  "status": "new",
  "channel": "unknown"
}
```

## 🔒 Segurança

### Prevenção de SQL Injection

✅ **Sempre usa placeholders (`?`)**

```python
# ✅ CORRETO
cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))

# ❌ ERRADO (vulnerável a SQL injection)
cursor.execute(f"SELECT * FROM appointments WHERE id = {appointment_id}")
```

### Validação de Dados

```python
# Validação é feita pelo Pydantic antes de chegar no banco
class Appointment(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(pattern=r'^\d{10,11}$')
    specialty: str = Field(min_length=3, max_length=100)
    # ...
```

## 🧪 Testes

### Testar Operações do Banco

```python
# tests/test_database.py

import pytest
from app.db.sqlite import (
    init_db, insert_appointment, get_appointment_by_id,
    list_appointments, count_appointments
)

@pytest.fixture
def test_db(tmp_path):
    """Cria banco de teste temporário"""
    db_path = tmp_path / "test.db"
    init_db(str(db_path))
    return str(db_path)

def test_insert_and_get(test_db):
    data = {
        "name": "João Silva",
        "phone": "11987654321",
        "specialty": "dermatologista",
        "preferred_datetime": "amanhã às 14h",
        "channel": "web"
    }
    
    # Inserir
    appointment_id = insert_appointment(data, test_db)
    assert appointment_id == 1
    
    # Buscar
    appointment = get_appointment_by_id(appointment_id, test_db)
    assert appointment["name"] == "João Silva"
    assert appointment["phone"] == "11987654321"

def test_list_appointments(test_db):
    # Inserir 3 agendamentos
    for i in range(3):
        data = {
            "name": f"Paciente {i}",
            "phone": f"1198765432{i}",
            "specialty": "dermatologista",
            "preferred_datetime": "amanhã",
        }
        insert_appointment(data, test_db)
    
    # Listar
    appointments = list_appointments(limit=10, offset=0, db_path=test_db)
    assert len(appointments) == 3
    
    # Paginação
    appointments_page1 = list_appointments(limit=2, offset=0, db_path=test_db)
    assert len(appointments_page1) == 2
    
    appointments_page2 = list_appointments(limit=2, offset=2, db_path=test_db)
    assert len(appointments_page2) == 1
```

## 📈 Performance

### Índices Otimizados

```sql
-- Busca por telefone (comum)
CREATE INDEX idx_appointments_phone ON appointments(phone);

-- Ordenação por data (comum)
CREATE INDEX idx_appointments_created_at ON appointments(created_at);
```

### Benchmarks

| Operação | Tempo Médio | Observação |
|----------|-------------|------------|
| `INSERT` | ~1ms | Com índices |
| `SELECT by ID` | ~0.5ms | Primary key |
| `SELECT by phone` | ~1ms | Com índice |
| `SELECT LIST (10)` | ~2ms | Com índice |

## 🔄 Migração para PostgreSQL (Futuro)

### Schema Equivalente

```sql
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    preferred_datetime TEXT NOT NULL,
    mode VARCHAR(20) DEFAULT 'nao_informado',
    reason TEXT,
    status VARCHAR(20) DEFAULT 'new',
    channel VARCHAR(20) DEFAULT 'unknown'
);

CREATE INDEX idx_appointments_phone ON appointments(phone);
CREATE INDEX idx_appointments_created_at ON appointments(created_at);
```

### Mudanças Necessárias

1. Trocar `sqlite3` por `psycopg2` ou `asyncpg`
2. Ajustar tipos de dados (TEXT → VARCHAR, INTEGER → SERIAL)
3. Usar `RETURNING id` em vez de `lastrowid`
4. Configurar connection pool

## 🛠️ Comandos Úteis

### Inspecionar Banco via CLI

```bash
# Abrir SQLite CLI
sqlite3 medagenda.db

# Listar tabelas
.tables

# Ver schema
.schema appointments

# Consultar dados
SELECT * FROM appointments;

# Contar registros
SELECT COUNT(*) FROM appointments;

# Sair
.quit
```

### Backup do Banco

```bash
# Criar backup
cp medagenda.db medagenda_backup_$(date +%Y%m%d).db

# Ou usar dump SQL
sqlite3 medagenda.db .dump > backup.sql
```

### Resetar Banco

```bash
# Deletar arquivo
rm medagenda.db

# Será recriado automaticamente na próxima execução
```

## 📚 Documentos Relacionados

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura geral
- **[AGENT_FLOW.md](./AGENT_FLOW.md)** - Como os dados são salvos
- **[API.md](./API.md)** - Endpoints que usam o banco

---

[← Voltar ao Índice](./INDEX.md)
