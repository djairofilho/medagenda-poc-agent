# 🚀 Guia de Instalação e Configuração

Este documento fornece instruções passo a passo para configurar e executar o MedAgenda Bot.

## 📋 Pré-requisitos

### Software Necessário

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** (opcional) - Para clonar o repositório
- **Editor de Código** (recomendado) - VS Code, PyCharm, etc.

### Verificar Instalação do Python

```powershell
python --version
# Deve mostrar: Python 3.11.x ou superior
```

## 🔧 Instalação

### Passo 1: Navegar até o Diretório do Projeto

```powershell
cd c:\Users\Usuario\Documents\programacao\MedAgenda\Bot
```

### Passo 2: Criar Ambiente Virtual

```powershell
python -m venv venv
```

### Passo 3: Ativar Ambiente Virtual

**Windows (PowerShell):**
```powershell
.\venv\Scripts\activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

Você verá `(venv)` no início da linha de comando:
```
(venv) PS C:\Users\Usuario\Documents\programacao\MedAgenda\Bot>
```

### Passo 4: Instalar Dependências

```powershell
pip install -r requirements.txt
```

**Dependências Instaladas:**
```
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
langgraph>=0.0.20
langchain-core>=0.1.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

### Passo 5: Instalar Streamlit (Opcional)

Para usar a interface web:

```powershell
pip install streamlit
```

### Passo 6: Verificar Instalação

```powershell
python -c "import fastapi, langgraph; print('OK')"
# Deve imprimir: OK
```

## 🚀 Executar o Projeto

### Opção 1: API Backend (FastAPI)

**Terminal 1:**

```powershell
# Ativar ambiente virtual
.\venv\Scripts\activate

# Rodar servidor
uvicorn app.main:app --reload --port 8000
```

**Saída Esperada:**
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\Usuario\\Documents\\programacao\\MedAgenda\\Bot']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Acessar:**
- API: `http://localhost:8000`
- Documentação: `http://localhost:8000/docs`

### Opção 2: Interface Streamlit

**Terminal 2** (manter Terminal 1 rodando):

```powershell
# Ativar ambiente virtual
.\venv\Scripts\activate

# Rodar Streamlit
streamlit run streamlit_app.py
```

**Saída Esperada:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

A interface abrirá automaticamente no navegador.

### Opção 3: Apenas Testes

```powershell
# Ativar ambiente virtual
.\venv\Scripts\activate

# Rodar testes
pytest tests/ -v
```

## ⚙️ Configuração

### Variáveis de Ambiente (Opcional)

Crie um arquivo `.env` na raiz do projeto:

```env
# Caminho do banco de dados
DB_PATH=medagenda.db

# Timeout de sessão (minutos)
SESSION_TIMEOUT_MINUTES=30

# Modo debug
DEBUG=true

# Porta da API
PORT=8000
```

**Carregar variáveis:**

```python
# app/config.py
from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "medagenda.db")
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

### Configurar Porta Diferente

```powershell
# Porta 8080 em vez de 8000
uvicorn app.main:app --reload --port 8080
```

### Configurar Host Externo

```powershell
# Aceitar conexões de qualquer IP
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

⚠️ **Atenção**: Apenas para desenvolvimento local. Em produção, use proxy reverso (nginx).

## 🗄️ Banco de Dados

### Inicialização Automática

O banco `medagenda.db` é criado automaticamente na primeira execução.

### Resetar Banco de Dados

```powershell
# Deletar banco existente
Remove-Item medagenda.db

# Será recriado automaticamente na próxima execução
```

### Inspecionar Banco de Dados

```powershell
# Instalar SQLite (se não tiver)
# Download: https://www.sqlite.org/download.html

# Abrir banco
sqlite3 medagenda.db

# Comandos úteis:
.tables                    # Listar tabelas
.schema appointments       # Ver schema
SELECT * FROM appointments; # Ver dados
.quit                      # Sair
```

## 🧪 Testes

### Rodar Todos os Testes

```powershell
pytest tests/ -v
```

### Rodar Testes Específicos

```powershell
# Apenas testes de extração
pytest tests/test_extract.py -v

# Apenas testes de fluxo
pytest tests/test_agent_flow.py -v
```

### Gerar Relatório de Cobertura

```powershell
pytest tests/ --cov=app --cov-report=html
```

Abre `htmlcov/index.html` no navegador para ver relatório.

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'langgraph'"

**Solução:**
```powershell
pip install --upgrade langgraph langchain-core
```

### Erro: "Permission denied: 'medagenda.db'"

**Solução:**
```powershell
# Fechar todas as conexões ao banco
# Ou deletar e recriar:
Remove-Item medagenda.db
```

### Erro: "Address already in use"

**Solução:**
```powershell
# Porta 8000 já está em uso
# Use porta diferente:
uvicorn app.main:app --reload --port 8001
```

### Erro: "Cannot activate virtual environment"

**Solução (PowerShell):**
```powershell
# Habilitar execução de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Tentar novamente
.\venv\Scripts\activate
```

### Streamlit não abre automaticamente

**Solução:**
```powershell
# Abrir manualmente no navegador:
# http://localhost:8501
```

## 🐳 Docker (Futuro)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./medagenda.db:/app/medagenda.db
    environment:
      - DB_PATH=/app/medagenda.db
```

### Executar com Docker

```bash
# Build
docker-compose build

# Run
docker-compose up
```

## 📦 Dependências Detalhadas

### Core

```
fastapi>=0.104.0        # Framework web
uvicorn>=0.24.0         # Servidor ASGI
pydantic>=2.5.0         # Validação de dados
```

### Agent

```
langgraph>=0.0.20       # Orquestração de fluxo
langchain-core>=0.1.0   # Core do LangChain
```

### Testing

```
pytest>=7.4.0           # Framework de testes
pytest-cov>=4.1.0       # Cobertura de código
```

### Optional

```
streamlit>=1.28.0       # Interface web
python-dotenv>=1.0.0    # Variáveis de ambiente
```

## 🔄 Atualizar Dependências

```powershell
# Atualizar todas as dependências
pip install --upgrade -r requirements.txt

# Atualizar dependência específica
pip install --upgrade fastapi
```

## 📝 Checklist de Instalação

- [ ] Python 3.11+ instalado
- [ ] Ambiente virtual criado
- [ ] Ambiente virtual ativado
- [ ] Dependências instaladas
- [ ] API rodando em `http://localhost:8000`
- [ ] Documentação acessível em `http://localhost:8000/docs`
- [ ] (Opcional) Streamlit rodando em `http://localhost:8501`
- [ ] Testes passando

## 📚 Próximos Passos

Após a instalação:

1. **Testar API**: Acesse `http://localhost:8000/docs`
2. **Ler Documentação**: Veja [USAGE.md](./USAGE.md) para exemplos
3. **Explorar Código**: Comece por [ARCHITECTURE.md](./ARCHITECTURE.md)
4. **Rodar Testes**: Execute `pytest tests/ -v`

## 📚 Documentos Relacionados

- **[USAGE.md](./USAGE.md)** - Exemplos de uso
- **[API.md](./API.md)** - Documentação da API
- **[TESTING.md](./TESTING.md)** - Guia de testes

---

[← Voltar ao Índice](./INDEX.md)
