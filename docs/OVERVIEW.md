# 🎯 Visão Geral - MedAgenda Bot

## O que é o MedAgenda?

**MedAgenda** é um agente conversacional inteligente projetado para automatizar o processo de agendamento de consultas médicas. Ele atua como uma "secretária virtual" que interage com pacientes através de linguagem natural para coletar informações e registrar pedidos de agendamento.

## 🎯 Objetivos do Projeto

### Objetivo Principal
Criar um assistente conversacional que simplifique o processo de agendamento de consultas médicas, reduzindo a carga de trabalho administrativo e melhorando a experiência do paciente.

### Objetivos Específicos

✅ **Coleta Inteligente de Dados**
- Extrair informações do paciente através de conversa natural
- Suportar múltiplos formatos de entrada (texto livre)
- Normalizar e validar dados automaticamente

✅ **Extração Sem LLM**
- Usar regex e heurísticas para extração rápida
- Evitar custos e latência de chamadas LLM
- Manter precisão aceitável para POC

✅ **Confirmação Antes de Salvar**
- Apresentar resumo dos dados coletados
- Permitir correções antes da confirmação
- Garantir precisão dos dados registrados

✅ **Persistência de Dados**
- Registrar agendamentos em banco SQLite
- Manter histórico de conversas por sessão
- Suportar consulta de agendamentos via API

❌ **Fora de Escopo**
- Diagnóstico médico
- Orientação de tratamento
- Prescrição de medicamentos
- Triagem clínica

## 🏗️ Arquitetura de Alto Nível

```
┌─────────────┐
│   Cliente   │ (Streamlit, WhatsApp, etc.)
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────────────────────────────────────┐
│          FastAPI Application                │
│  ┌────────────────────────────────────────┐ │
│  │      LangGraph Agent                   │ │
│  │  ┌──────────────────────────────────┐  │ │
│  │  │  1. Extract Fields               │  │ │
│  │  │  2. Ask Missing / Confirm        │  │ │
│  │  │  3. Handle Confirmation & Save   │  │ │
│  │  └──────────────────────────────────┘  │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │      Session Management                │ │
│  │      (In-Memory Dict)                  │ │
│  └────────────────────────────────────────┘ │
└──────┬───────────────────────────────────────┘
       │
       │ SQLite
       │
┌──────▼──────────┐
│  medagenda.db   │
│  - appointments │
└─────────────────┘
```

## 🛠️ Stack Tecnológica

### Backend
- **Python 3.11+** - Linguagem principal
- **FastAPI** - Framework web moderno e rápido
- **LangGraph** - Orquestração do fluxo conversacional
- **Pydantic** - Validação de dados e schemas
- **SQLite** - Banco de dados leve e sem dependências
- **Uvicorn** - Servidor ASGI de alta performance

### Frontend/Interface
- **Streamlit** - Interface web interativa para testes
- **Markdown** - Formatação de mensagens

### Testes
- **Pytest** - Framework de testes
- **pytest-cov** - Cobertura de código

## 📊 Fluxo de Dados

```
1. Usuário envia mensagem
   ↓
2. FastAPI recebe via POST /chat
   ↓
3. LangGraph processa através dos nós:
   a) Extrai campos da mensagem
   b) Identifica campos faltantes
   c) Gera resposta apropriada
   ↓
4. Se confirmado → Salva no SQLite
   ↓
5. Retorna resposta ao usuário
```

## 🎭 Personas e Casos de Uso

### Persona 1: Paciente Novo
**Cenário**: Primeira consulta, fornece todas as informações de uma vez
```
Usuário: "Oi, me chamo João Silva, telefone 11 98765-4321, 
         quero marcar dermatologista presencial amanhã às 14h"
         
Bot: [Confirma dados e agenda]
```

### Persona 2: Paciente Gradual
**Cenário**: Fornece informações aos poucos
```
Usuário: "Quero marcar consulta"
Bot: "Qual especialidade?"
Usuário: "Cardiologista"
Bot: "Qual seu nome?"
[... continua até coletar tudo]
```

### Persona 3: Paciente com Dúvida Médica
**Cenário**: Tenta obter diagnóstico (fora de escopo)
```
Usuário: "Estou com dor no peito, o que pode ser?"
Bot: "Eu só ajudo a marcar consulta. Você quer agendar 
     com qual especialidade?"
```

## 🔒 Princípios de Segurança

1. **Escopo Restrito**: Apenas agendamento, sem orientação médica
2. **Detecção de Urgências**: Alerta para buscar atendimento imediato
3. **Validação de Dados**: Campos obrigatórios e formatos esperados
4. **Confirmação Explícita**: Usuário revisa antes de salvar

## 📈 Métricas de Sucesso (POC)

- ✅ Taxa de conclusão de agendamento > 80%
- ✅ Tempo médio de conversa < 2 minutos
- ✅ Precisão de extração de campos > 85%
- ✅ Zero casos de orientação médica inadequada

## 🚀 Roadmap Futuro

### Fase 2 (Pós-POC)
- [ ] Integração com WhatsApp Business API
- [ ] Validação de slots de horário disponíveis
- [ ] Sistema de notificações (SMS/Email)
- [ ] Dashboard administrativo

### Fase 3 (Produção)
- [ ] Autenticação e autorização
- [ ] Multi-tenancy (múltiplas clínicas)
- [ ] Integração com sistemas de prontuário
- [ ] Analytics e relatórios

## 📚 Documentos Relacionados

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detalhes da arquitetura
- **[AGENT_FLOW.md](./AGENT_FLOW.md)** - Fluxo do agente LangGraph
- **[SECURITY.md](./SECURITY.md)** - Restrições de segurança

---

[← Voltar ao Índice](./INDEX.md)
