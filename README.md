# medAgenda Agent

POC de atendimento para uma clínica fictícia. O FastAPI expõe chat, consultas e horários; o LangGraph conduz a conversa; PostgreSQL guarda dados da clínica e checkpoints; Langfuse é opcional para observabilidade e experimentos.

> Use somente dados fictícios. A API ainda não tem autenticação para pacientes reais.

## Estrutura

```text
app/
  conversations/   # grafo, estado, roteamento, triagem e chat HTTP
  appointments/    # reserva transacional e leitura de consultas
  availability/    # cadastro e consulta de horários
  patients/        # validação de CPF e telefone
  clinic/          # contexto administrativo
  infrastructure/  # engine SQLAlchemy e modelos ORM
  observability/   # traces Langfuse com conteúdo mascarado
  evals/           # runner e juiz opcional
tests/             # testes separados pelas mesmas funcionalidades
alembic/           # versão do esquema PostgreSQL
```

`main.py` monta a aplicação e registra os routers. Os caminhos e formatos HTTP existentes continuam disponíveis, inclusive `POST /chat` e `POST /sessions/{session_id}/reset`, usados pelo Streamlit.

## Executar localmente

Requer Python 3.11+, Docker e Docker Compose.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d postgres
alembic upgrade head
python -m scripts.seed_demo
uvicorn app.main:app --reload
```

Preencha `GOOGLE_API_KEY` com `LLM_PROVIDER=gemini`, ou use `LLM_PROVIDER=openai` com `OPENAI_API_KEY`. A API inicia sem chave, mas `/chat` devolve 503 até configurar um modelo. A interface pode ser iniciada com `streamlit run streamlit_app.py`.

O banco de dados desta versão é PostgreSQL. O `DATABASE_URL` usa o driver SQLAlchemy `postgresql+psycopg`; o `CHECKPOINT_DATABASE_URL` usa `postgresql` para o checkpointer do LangGraph. O Compose fornece ambos no mesmo PostgreSQL local. O esquema é criado pelo Alembic; `seed_demo` adiciona dados fictícios, incluindo horários futuros.

## Fluxo de agendamento

O agente coleta especialidade, horário exato cadastrado, nome, CPF válido, telefone e modalidade. Ele apresenta um resumo sem CPF completo e exige confirmação explícita. O serviço de consultas reserva o slot e grava a consulta na mesma transação; respostas de sucesso usam o ID salvo. Repetir a confirmação retorna o mesmo agendamento.

O estado da conversa é persistido pelo `PostgresSaver`. Reiniciar a API mantém a sessão; `POST /sessions/{session_id}/reset` remove seus checkpoints. A verificação de emergência ocorre antes do roteamento por modelo. A POC não oferece diagnóstico.

## Langfuse e evals

Defina `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` e, se necessário, `LANGFUSE_BASE_URL`. Sem as duas chaves, a aplicação não cria traces. Com elas, cada mensagem gera um trace agrupado por um hash do ID da sessão. O exportador remove atributos de texto livre, incluindo prompts, respostas e conteúdo clínico; métricas numéricas e dimensões controladas continuam disponíveis. Instalações próprias devem usar uma versão do Langfuse compatível com o SDK Python v5.

```powershell
python -m pytest -q tests
python -m scripts.run_evals
python -m scripts.run_evals --publish
python -m scripts.run_evals --publish --live-model --judge
```

O runner usa bancos temporários no PostgreSQL local e um dataset sintético versionado em `tests/evals/dataset.json`. Sem opções, usa um modelo simulado e falha se uma regra crítica regredir. `--publish` publica experimento e scores objetivos no Langfuse. `--live-model` testa o provedor configurado; `--judge` acrescenta uma nota qualitativa de clareza e aderência somente ao experimento. O juiz não bloqueia a validação. Nenhum desses comandos usa o banco principal para os casos de avaliação.
Os itens publicados contêm o ID do cenário e as métricas calculadas; mensagens e respostas ficam no processo local. A publicação remota exige credenciais Langfuse válidas.

## Endpoints principais

| Método | Caminho | Função |
| --- | --- | --- |
| POST | `/chat` | Processa uma mensagem |
| POST | `/sessions/{session_id}/reset` | Reinicia a conversa |
| GET | `/appointments` | Lista consultas, com paginação |
| GET | `/appointments/{id}` | Consulta por ID |
| GET, POST, DELETE | `/slots` | Consulta e administra horários |

O contrato OpenAPI está em `/docs`. Os endpoints administrativos fazem parte da POC e precisam de autenticação antes de qualquer uso com pacientes reais.
