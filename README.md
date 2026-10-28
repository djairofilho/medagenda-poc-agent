# medAgenda Agent

POC de atendimento para uma clínica fictícia. O FastAPI expõe chat, consultas e horários; o LangGraph conduz a conversa; PostgreSQL ou SQLite guarda dados da clínica e checkpoints; Langfuse é opcional para observabilidade e experimentos.

> Use somente dados fictícios. A API ainda não tem autenticação para pacientes reais.

## Estrutura

```text
app/
  conversations/   # grafo, estado, roteamento, triagem e chat HTTP
  appointments/    # reserva transacional e leitura de consultas
  availability/    # cadastro e consulta de horários
  patients/        # validação de CPF e telefone
  clinic/          # contexto administrativo
  infrastructure/  # adapters SQLAlchemy e LangGraph para PostgreSQL/SQLite
  observability/   # traces Langfuse com conteúdo mascarado
  evals/           # runner e juiz opcional
tests/             # testes separados pelas mesmas funcionalidades
alembic/           # versão do esquema relacional
```

`main.py` monta a aplicação e registra os routers. Os caminhos e formatos HTTP existentes continuam disponíveis, inclusive `POST /chat` e `POST /sessions/{session_id}/reset`, usados pelo Streamlit.

O diagrama do grafo fica em `docs/`. Para atualizar o Mermaid e o PNG, execute `uv run --locked python -m scripts.generate_graph_diagram` na raiz do projeto.

## Executar localmente

Requer Python 3.11+ e [uv](https://docs.astral.sh/uv/getting-started/installation/). O fluxo padrão com PostgreSQL usa Docker e Docker Compose. `pyproject.toml` declara as dependências e `uv.lock` fixa suas versões.

```powershell
uv sync --locked
Copy-Item .env.example .env
docker compose up -d postgres
uv run --locked alembic upgrade head
uv run --locked python -m scripts.seed_demo
uv run --locked uvicorn app.main:app --reload
```

Preencha `GOOGLE_API_KEY` com `LLM_PROVIDER=gemini`, ou use `LLM_PROVIDER=openai` com `OPENAI_API_KEY`. A API inicia sem chave, mas `/chat` devolve 503 até configurar um modelo. A interface pode ser iniciada com `uv run --locked streamlit run streamlit_app.py`.

Para uma demonstração local com o login do Codex CLI, use `LLM_PROVIDER=codex` em `.env` e confira `codex login status`. O adaptador usa `CODEX_MODEL=gpt-6-luna` e `CODEX_REASONING_EFFORT=low` por padrão; essas opções podem ser alteradas em `.env`. Cada etapa do modelo inicia um processo `codex exec`, então o chat pode continuar lento. Use essa opção apenas em uma máquina confiável e mantenha a API acessível somente em `127.0.0.1`.

`DATABASE_URL` escolhe o banco para consultas, pacientes e horários. O adapter escolhe o checkpointer correspondente do LangGraph. Por padrão, `CHECKPOINT_DATABASE_URL` usa o mesmo banco; é possível defini-lo separadamente. Para PostgreSQL, use `postgresql+psycopg://...`; para SQLite, use `sqlite+pysqlite:///./medagenda.db`. O esquema relacional é criado pelo Alembic; `seed_demo` adiciona dados fictícios, incluindo horários futuros.

Para executar tudo em SQLite, altere `.env` para `DATABASE_URL=sqlite+pysqlite:///./medagenda.db`, deixe `CHECKPOINT_DATABASE_URL` sem valor e execute os três comandos `uv run` acima. O Compose não é necessário nesse caso. Os checkpoints do SQLite ficam no mesmo arquivo `.db`. Para voltar ao PostgreSQL, restaure as URLs do exemplo e inicie o serviço do Compose. A troca de URL não transfere registros entre bancos.

## Fluxo de agendamento

O agente coleta especialidade, horário exato cadastrado, nome, CPF válido, telefone e modalidade. Ele apresenta um resumo sem CPF completo e exige confirmação explícita. O serviço de consultas reserva o slot e grava a consulta na mesma transação; respostas de sucesso usam o ID salvo. Repetir a confirmação retorna o mesmo agendamento.

O estado da conversa é persistido pelo `PostgresSaver` ou `SqliteSaver`, conforme a URL. Reiniciar a API mantém a sessão; `POST /sessions/{session_id}/reset` remove seus checkpoints. A verificação de emergência ocorre antes do roteamento por modelo. A POC não oferece diagnóstico. PostgreSQL continua recomendado para maior concorrência; SQLite serializa as transações de reserva.

## Langfuse e evals

Defina `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` e, se necessário, `LANGFUSE_BASE_URL`. Defina também `LANGFUSE_TRACING_ENVIRONMENT=production` no serviço para filtrar o painel de produção. Sem as duas chaves, a aplicação não cria traces. Com elas, cada mensagem gera um trace agrupado por um hash do ID da sessão. O exportador remove atributos de texto livre, incluindo prompts, respostas e conteúdo clínico; métricas numéricas e dimensões controladas continuam disponíveis. Instalações próprias devem usar uma versão do Langfuse compatível com o SDK Python v5. O [guia de monitoramento](docs/observability.md) especifica widgets e alertas para recriação manual.

Publique as quatro versões iniciais com o rótulo `production` somente quando quiser ativá-las no projeto Langfuse configurado:

```powershell
uv run --locked python -m scripts.publish_prompts --publish
```

O comando não faz parte do CI. Sem uma versão acessível, cada adaptador usa o prompt local correspondente.

```powershell
uv run --locked python -m pytest -q tests
uv run --locked python -m scripts.run_evals
uv run --locked python -m scripts.run_evals --publish
uv run --locked python -m scripts.run_evals --publish --live-model --judge
```

Ao alterar dependências, use `uv add`, `uv add --dev` ou edite `pyproject.toml` e execute `uv lock`. Versione `pyproject.toml` e `uv.lock` juntos.

O runner usa bancos temporários no backend configurado e um dataset sintético versionado em `tests/evals/dataset.json`. Sem opções, usa um modelo simulado e falha se uma regra crítica regredir. O CI executa essas verificações em PostgreSQL e SQLite. `--publish` publica experimento e scores objetivos no Langfuse. `--live-model` testa o provedor configurado; `--judge` acrescenta uma nota qualitativa de clareza e aderência somente ao experimento. Modelo real e publicação são operações manuais ou agendadas e não bloqueiam cada PR. Nenhum desses comandos usa o banco principal para os casos de avaliação.

Os itens publicados contêm somente o ID do cenário, resultados controlados e métricas calculadas; mensagens e respostas ficam no processo local. Os metadados da execução incluem versões do código, dos prompts e do dataset. A publicação remota exige credenciais Langfuse válidas.

## Endpoints principais

| Método | Caminho | Função |
| --- | --- | --- |
| POST | `/chat` | Processa uma mensagem |
| POST | `/sessions/{session_id}/reset` | Reinicia a conversa |
| GET | `/appointments` | Lista consultas, com paginação |
| GET | `/appointments/{id}` | Consulta por ID |
| GET, POST, DELETE | `/slots` | Consulta e administra horários |

O contrato OpenAPI está em `/docs`. Os endpoints administrativos fazem parte da POC e precisam de autenticação antes de qualquer uso com pacientes reais.
