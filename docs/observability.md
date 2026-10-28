# Monitoramento do medAgenda no Langfuse

Este guia reproduz o painel e os dois alertas na interface do projeto. Use uma
instância compatível com o SDK Python v5. Nenhum widget requer prompts, respostas,
nome, CPF, telefone ou conteúdo clínico. O medAgenda exporta dimensões controladas
(`route`, `phase`, `booking_status`, `technical_success`, `error_category`,
`model`, `prompt_name`, `prompt_version`, `prompt_source`), tipo de observação,
modelo e uso de tokens. Cada turno gera um trace `medagenda-chat`.

## Preparação

1. Configure `LANGFUSE_TRACING_ENVIRONMENT=production` no serviço antes de
   iniciar o SDK. Sem essa variável, o ambiente é `default`.
2. Abra **Dashboards > Widgets > New Widget** no projeto. Crie os widgets da
   tabela abaixo e depois **Dashboards > New Dashboard**, com o nome
   `medAgenda | operação`. Adicione todos os widgets.
3. No seletor do painel, escolha **Environment = production** e **Last 24 hours**.
   Deixe cada widget sem filtro próprio de ambiente: um filtro no widget
   substituiria o seletor do painel. Para análise por modelo, filtre o campo de
   modelo da geração; para rota, filtre `metadata.route` do span raiz. Use
   `scheduling`, `information` ou `triage`.

| Widget | Fonte e filtro fixo | Medida e dimensão | Gráfico |
| --- | --- | --- | --- |
| Turnos por hora | Observations; `name = medagenda-chat`; `type = span`; observação raiz | `count` por hora; agrupar por `metadata.route` | Série temporal empilhada |
| Latência do turno | Observations; `name = medagenda-chat`; `type = span`; observação raiz | `p50 latency` e `p95 latency` por hora | Duas séries temporais |
| Gerações por modelo | Observations; `type = generation` | `count` por modelo | Barras |
| Tokens de entrada | Observations; `type = generation` | `sum input tokens` por hora e modelo | Série temporal empilhada |
| Tokens de saída | Observations; `type = generation` | `sum output tokens` por hora e modelo | Série temporal empilhada |
| Custo do modelo | Observations; `type = generation` | `sum total cost` por hora e modelo | Série temporal empilhada |
| Sucesso técnico | Scores (boolean); `name = technical_success` | `avg value` por hora, em porcentagem | Série temporal |
| Falhas por categoria | Observations; `name = medagenda-chat`; `type = span`; `level = ERROR` | `count` por hora e `metadata.error_category` | Série temporal empilhada |
| Resultado da reserva | Observations; `name = medagenda-chat`; `type = span`; observação raiz; `metadata.route = scheduling` | `count` por `metadata.booking_status` e hora | Série temporal empilhada |
| Integridade da reserva | Scores (boolean); `name = booking_integrity` | `avg value` por hora, em porcentagem | Série temporal |

Para volume e latência, contar apenas o span raiz evita multiplicar um turno
pelas gerações e etapas internas. O filtro por modelo pertence aos widgets de
geração; os spans de turno têm o modelo solicitado em `metadata.model`. O custo
só aparece se o modelo/SDK fornecer preços reconhecidos pelo Langfuse; tokens
continuam úteis quando o custo não estiver disponível. Os scores de reserva
são emitidos apenas em turnos com tentativa. `no_attempt` aparece no widget de
resultado, mas fica fora do denominador de `booking_integrity`. Nesse score,
`true` significa que o resultado da tentativa e a fase final concordam;
`booking_confirmed` mede separadamente a fração das tentativas que confirmaram.

## Alertas

Em **Alerts > New Alert**, crie os dois itens abaixo. Selecione a automação de
notificação existente do projeto; um Admin ou Owner configura a automação em
**Automations**. Use **Show severity NO_DATA** para ausência de amostras e
**Renotify = Off**, para não interpretar silêncio como taxa zero.

| Nome | Fonte e filtro | Métrica | Condição | Janela |
| --- | --- | --- | --- | --- |
| `medAgenda | sucesso técnico` | Scores (boolean), `name = technical_success`, `environment = production` | `avg value` | `< 0.99` | 1 hora |
| `medAgenda | integridade da reserva` | Scores (boolean), `name = booking_integrity`, `environment = production` | `avg value` | `< 1.00` | 1 hora |

O primeiro alerta usa todos os turnos. O segundo usa somente turnos com
tentativa de reserva; um único resultado incoerente viola o limite inicial.
Após duas a quatro semanas de tráfego real, revise volume mínimo, falsos
positivos, janela e limites com a equipe operacional, preservando o histórico
das mudanças. Em instalações sem suporte a Alerts, mantenha os mesmos dois
widgets e faça a verificação periódica manualmente.

## Evals e publicação

`uv run --locked python -m scripts.run_evals` executa o dataset sintético em
um banco temporário no backend configurado. O CI roda esse comando em
PostgreSQL e SQLite e bloqueia o PR se uma regra determinística falhar. Casos
de serviço cobrem `booked`, `already_booked`, `unavailable` e `invalid`;
casos de conversa verificam `no_attempt`, resultado por turno e ausência de
confirmação falsa. Os quatro prompts verificam a versão `production` e o
fallback local sem rede.

`--live-model` e `--publish` são comandos manuais ou próprios de um agendamento
com credenciais; nenhum PR chama a API de modelo real ou publica no Langfuse.
O experimento remoto recebe somente IDs de cenários, resultados controlados e
scores, com `code_version` (SHA do commit), `prompt_version` (versão local
do pacote), `prompt_versions` (versão efetiva de cada um dos quatro prompts),
`dataset_version` (SHA-256 abreviado do arquivo) e `model` nos metadados.
As mensagens sintéticas e respostas ficam no processo local. `--judge` aplica
avaliação qualitativa apenas a esses dados sintéticos e não bloqueia o CI.

## Referências

- [Custom Dashboards](https://langfuse.com/docs/metrics/features/custom-dashboards)
- [Alerts](https://langfuse.com/docs/observability/features/alerts)
- [Environments](https://langfuse.com/docs/observability/features/environments)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
