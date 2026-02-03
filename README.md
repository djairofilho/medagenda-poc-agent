# 🏥 medAgenda Agent

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)](https://github.com/langchain-ai/langgraph)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**medAgenda** é um sistema de multi-agentes orquestrado com **LangGraph** para automação de clínicas médicas, lidando desde triagem até agendamento de consultas.

---

## 🏗️ Arquitetura (LangGraph)

O bot utiliza uma estrutura de agentes especializados coordenados por um roteador central:

![Fluxo de Agentes](langgraph_diagram.png)

### Agentes:
- 🧭 **Router**: Identifica a intenção do usuário e direciona para o agente correto.
- 🩺 **Triage**: Avalia sintomas e fornece orientações de segurança (sem diagnóstico).
- 📅 **Scheduling**: Gerencia a coleta de dados e persistência de agendamentos no SQLite.
- ℹ️ **Information**: Responde dúvidas sobre endereço, convênios e preços.

---

## 🛠️ Stack Tecnológica

- **LangGraph** (Orquestração)
- **FastAPI** (Backend API)
- **Pydantic** (Validação de Dados)
- **Streamlit** (Interface Web)
- **SQLite** (Banco de Dados)

---

## 🚀 Como Rodar

### 1. Preparar Ambiente
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar `.env`
```bash
LLM_PROVIDER=gemini # ou openai, anthropic
GOOGLE_API_KEY=sua_chave_aqui
```

### 3. Iniciar Aplicação
**Backend:**
```bash
uvicorn app.main:app --reload
```

**Frontend (Web):**
```bash
streamlit run streamlit_app.py
```

---

## 📡 Endpoints Principais

- `POST /chat`: Interação com o agente.
- `GET /appointments`: Lista agendamentos realizados.
- `GET /docs`: Documentação Swagger completa.



