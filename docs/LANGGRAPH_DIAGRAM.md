# 📊 Diagrama do LangGraph - MedAgenda Bot

## 🖼️ Visualização

![LangGraph Diagram](../langgraph_diagram.png)

## 📝 Descrição dos Nós

### **__start__**
Ponto de entrada do grafo quando uma nova mensagem chega.

### **extract**
**Nó:** `node_extract_fields`

Extrai informações da mensagem do usuário:
- Usa PydanticAI (LLM) para extração estruturada
- Fallback para Regex se LLM falhar
- Merge inteligente dos resultados
- Detecta intent: `schedule`, `info`, `urgent`, `out_of_scope`

### **check_onboarding**
**Nó:** `node_check_onboarding`

Verifica se o usuário já está cadastrado:
- Busca paciente por telefone no banco de dados
- Se encontrado: carrega dados e pula onboarding
- Se não encontrado: inicia processo de cadastro

### **provide_info**
**Nó:** `node_provide_clinic_info`

Fornece informações sobre a clínica:
- Endereço, horário, serviços, convênios, etc.
- Resposta contextual baseada na pergunta
- Termina o fluxo (usuário pode iniciar novo agendamento)

### **ask_or_confirm**
**Nó:** `node_ask_missing_or_confirm`

Gerencia coleta de dados e confirmação:

**Onboarding (novo paciente):**
1. Pergunta nome
2. Pergunta telefone
3. Salva paciente no banco

**Agendamento:**
1. Pergunta especialidade
2. Pergunta data/horário
3. Pergunta modo (presencial/online)
4. Gera confirmação

### **handle_confirmation**
**Nó:** `node_handle_confirmation_and_save`

Processa confirmação do usuário:
- Se "sim": salva agendamento no banco
- Se "não": permite ajustes
- Retorna mensagem de sucesso ou pedido de correção

### **__end__**
Fim do fluxo. Conversa encerrada.

---

## 🔀 Fluxos Possíveis

### Fluxo 1: Pedido de Informações
```
start → extract → provide_info → end
```

### Fluxo 2: Novo Paciente (Onboarding + Agendamento)
```
start → extract → check_onboarding → ask_or_confirm (nome)
      → extract → check_onboarding → ask_or_confirm (phone)
      → extract → check_onboarding → ask_or_confirm (especialidade)
      → extract → check_onboarding → ask_or_confirm (datetime)
      → extract → check_onboarding → ask_or_confirm (modo)
      → extract → check_onboarding → ask_or_confirm (confirmação)
      → extract → check_onboarding → ask_or_confirm → handle_confirmation → end
```

### Fluxo 3: Paciente Retornando (Apenas Agendamento)
```
start → extract → check_onboarding (encontrou!) → ask_or_confirm (especialidade)
      → extract → check_onboarding → ask_or_confirm (datetime)
      → extract → check_onboarding → ask_or_confirm (modo)
      → extract → check_onboarding → ask_or_confirm (confirmação)
      → extract → check_onboarding → ask_or_confirm → handle_confirmation → end
```

---

## 🔄 Como Regenerar o Diagrama

Execute o script:

```bash
python generate_graph_diagram.py
```

Isso irá:
1. ✅ Gerar `docs/langgraph_diagram.mmd` (código Mermaid)
2. ✅ Gerar `docs/langgraph_diagram.png` (imagem PNG)

### Alternativas

**Opção 1: Mermaid Live Editor**
1. Acesse: https://mermaid.live/
2. Cole o conteúdo de `langgraph_diagram.mmd`
3. Exporte como PNG/SVG

**Opção 2: Mermaid CLI (local)**
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/langgraph_diagram.mmd -o docs/langgraph_diagram.png
```

---

## 📚 Documentação Relacionada

- [AGENT_FLOW.md](AGENT_FLOW.md) - Fluxo detalhado do agente
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitetura geral
- [PYDANTIC_AI.md](PYDANTIC_AI.md) - Integração PydanticAI

---

**Última atualização:** 2026-01-28
