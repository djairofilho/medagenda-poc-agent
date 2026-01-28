# 🤖 Integração PydanticAI - MedAgenda Bot

Este documento detalha a integração do PydanticAI como camada de extração estruturada no MedAgenda Bot.

## 🎯 Objetivo

Usar PydanticAI para extração estruturada de dados de mensagens naturais, mantendo:
- ✅ LangGraph como orquestrador do fluxo
- ✅ SQLite como persistência
- ✅ Suporte multi-provider (Gemini/OpenAI/Anthropic)
- ✅ Fallback automático para regex
- ✅ Restrições de segurança (sem orientação médica)

## 🏗️ Arquitetura

```
User Message
    ↓
┌───────────────────────────────────────┐
│  node_extract_fields (LangGraph)      │
│                                       │
│  1. PydanticAI Extraction             │
│     ├─ Gemini / OpenAI / Anthropic    │
│     └─ Returns ExtractResult          │
│                                       │
│  2. Regex Extraction (Fallback)       │
│     └─ Returns dict                   │
│                                       │
│  3. Merge Strategy                    │
│     ├─ Regex wins: phone, mode        │
│     ├─ LLM wins: name, specialty, etc │
│     └─ Fill gaps intelligently        │
│                                       │
│  4. Update State                      │
│     └─ Convert to dict for LangGraph  │
└───────────────────────────────────────┘
    ↓
Continue LangGraph Flow
```

## 📦 Módulo Extractor

### Estrutura

```
app/agent/extractor/
├── __init__.py       # Exports public interface
├── schema.py         # ExtractResult (Pydantic model)
├── prompts.py        # SYSTEM_INSTRUCTIONS (single prompt)
├── factory.py        # Multi-provider agent creation
├── adapter.py        # Main extraction interface
└── merge.py          # LLM + regex merge logic
```

### Schema: ExtractResult

**Source of truth** para todos os dados extraídos:

```python
class ExtractResult(BaseModel):
    # Flags
    out_of_scope: bool = False
    urgent_flag: bool = False
    
    # Patient data
    name: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    preferred_datetime: Optional[str] = None
    mode: AppointmentMode = AppointmentMode.NAO_INFORMADO
    reason: Optional[str] = None
    
    # Metadata
    confidence: float = 0.5  # 0.0 to 1.0
```

**Validações automáticas:**
- Trim de strings
- Clamp de confidence (0.0 a 1.0)
- Truncate de reason (max 100 chars)
- Conversão de strings vazias para None

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Provider selection
LLM_PROVIDER=gemini  # gemini|openai|anthropic|fallback

# Gemini
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
```

### Providers Suportados

| Provider | Model Default | Custo/10k msgs |
|----------|---------------|----------------|
| **Gemini** | gemini-1.5-flash | ~$0.40 |
| **OpenAI** | gpt-4o-mini | ~$1.50 |
| **Anthropic** | claude-3-5-haiku | ~$1.00 |
| **Fallback** | Regex | $0.00 |

## 🔀 Estratégia de Merge

### Regras de Precedência

1. **Regex VENCE** para:
   - `phone` - Regex é mais confiável para padrões BR
   - `mode` - Keywords são determinísticas

2. **LLM VENCE** para:
   - `name` - Melhor compreensão de nomes compostos
   - `specialty` - Normalização de variações
   - `preferred_datetime` - Entende contexto temporal
   - `reason` - Extração semântica

3. **Flags SEMPRE do LLM**:
   - `out_of_scope` - Detecção de intent
   - `urgent_flag` - Detecção de urgência

4. **Preenchimento de Gaps**:
   - Se LLM não extraiu campo, usa regex
   - Se ambos extraíram, segue regras de precedência

### Exemplo de Merge

```python
# Input
user_text = "Sou João Silva, zap 11987654321, preciso dermato amanhã"

# LLM Result
llm_result = ExtractResult(
    name="João Silva",
    phone="11987654321",  # Pode ter erro
    specialty="dermatologista",
    preferred_datetime="amanhã",
    confidence=0.9
)

# Regex Result
regex_result = {
    'phone': '11987654321',  # Mais confiável
    'mode': 'nao_informado',
}

# Merged Result
merged = ExtractResult(
    name="João Silva",           # LLM
    phone="11987654321",          # Regex (venceu)
    specialty="dermatologista",   # LLM
    preferred_datetime="amanhã",  # LLM
    mode="nao_informado",         # Regex (venceu)
    confidence=0.9
)
```

## 🔒 Segurança

### Prompt Engineering

O prompt único (`SYSTEM_INSTRUCTIONS`) reforça:

```
Você é o medAgenda, um assistente de AGENDAMENTO.

ESCOPO RESTRITO:
- Você APENAS ajuda a agendar consultas
- Você NÃO pode dar diagnóstico
- Você NÃO pode dar tratamento
- Você NÃO pode dar orientação médica

REGRAS:
1. Se pedir diagnóstico → out_of_scope=true
2. Se sintomas urgentes → urgent_flag=true
3. Sintomas para contexto → reason (max 100 chars)
```

### Flags de Controle

**out_of_scope=true**
```
Input: "O que pode ser essa dor de cabeça?"
Output: ExtractResult(out_of_scope=True, ...)
Bot: "Eu só ajudo a marcar consulta. Você quer agendar com qual especialidade?"
```

**urgent_flag=true**
```
Input: "Estou com dor no peito forte"
Output: ExtractResult(urgent_flag=True, reason="dor no peito", ...)
Bot: "Posso ajudar a agendar, mas se urgente procure atendimento imediato."
```

## 🔄 Fallback Automático

### Quando Ocorre

1. **Sem API key configurada**
   ```python
   LLM_PROVIDER=fallback
   # ou
   GOOGLE_API_KEY não definido
   ```

2. **Provider falha**
   ```python
   # Timeout, erro de API, etc.
   # Automaticamente retorna ExtractResult(confidence=0.0)
   ```

3. **Resposta inválida**
   ```python
   # Pydantic validation falha
   # Retries (max 2) não resolvem
   # Fallback para regex
   ```

### Comportamento

```python
# LLM falhou → confidence=0.0
llm_result = ExtractResult(confidence=0.0)

# Merge usa 100% regex
merged = merge_extractions(llm_result, regex_result)
# merged.name = regex_result['name']
# merged.phone = regex_result['phone']
# etc.

# Confidence recalculada baseado em campos preenchidos
# merged.confidence = (campos_preenchidos / 4) * 0.8
```

## 🧪 Testes

### Executar Testes

```bash
# Testes de schema
pytest tests/test_extractor_schema.py -v

# Testes de merge
pytest tests/test_extractor_merge.py -v

# Todos os testes
pytest tests/ -v
```

### Casos de Teste Principais

1. **Schema Validation**
   - Trim de strings
   - Clamp de confidence
   - Truncate de reason
   - Enum de mode

2. **Merge Logic**
   - Regex vence phone/mode
   - LLM vence campos semânticos
   - Preenchimento de gaps
   - Recálculo de confidence

3. **Fallback**
   - LLM falhou → usa regex
   - Provider inválido → fallback
   - Sem API key → fallback

## 📊 Performance

### Latência Esperada

| Cenário | Latência |
|---------|----------|
| LLM (Gemini Flash) | ~500ms - 2s |
| LLM (OpenAI Mini) | ~300ms - 1s |
| LLM (Anthropic Haiku) | ~400ms - 1.5s |
| Fallback (Regex) | < 50ms |

### Otimizações

1. **Timeout de 5s** - Evita espera infinita
2. **Retries (max 2)** - Corrige respostas inválidas
3. **Fallback automático** - Sempre funciona
4. **Modelos rápidos** - Flash, Mini, Haiku

## 🔍 Troubleshooting

### LLM não está sendo usado

```bash
# Verificar configuração
echo $LLM_PROVIDER
echo $GOOGLE_API_KEY

# Logs
# [Adapter] No agent configured, using fallback
# → Provider não configurado ou API key ausente
```

### Extração incorreta

```bash
# Verificar merge
# [Merge] Using regex phone: 11987654321
# [Merge] Filled specialty from regex: dermatologista

# Se regex está vencendo muito, LLM pode estar falhando
# Verificar logs de erro
```

### Custos altos

```bash
# Usar modelo mais barato
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash  # Mais barato

# Ou fallback
LLM_PROVIDER=fallback  # Grátis
```

## 📚 Documentos Relacionados

- **[EXTRACTION.md](./EXTRACTION.md)** - Detalhes de extração regex
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Arquitetura geral
- **[SECURITY.md](./SECURITY.md)** - Restrições de segurança

---

[← Voltar ao Índice](./INDEX.md)
