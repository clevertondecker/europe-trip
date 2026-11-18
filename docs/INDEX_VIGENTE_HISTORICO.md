# Índice documental — Nossa Europa 2027

**Atualizado:** 18/11/2026 · **referência:** `main` após DATA 8 e DATA 9.1.

Este índice distingue **documentação operacional vigente**, **snapshots de pesquisa** e **relatórios históricos**. A data e o estado indicados abaixo não significam que uma rota, preço, horário ou reserva sejam válidos para 2027.

## Fonte da verdade por assunto

| Assunto | Documento/código a consultar | Estado |
|---|---|---|
| Como executar e navegar | [README.md](../README.md) e `app.py` | Vigente; comportamento do código prevalece |
| Roteiro aprovado e estado da sessão | `trip_plan_model.py`, `planning_session.py`, `planning_store.py` | Contrato vigente; não modificar por leitura exploratória |
| Evidência histórica ferroviária | `evidence_query_model.py`, `rail_evidence_unified_model.py`, `routes7_reference_model.py` | Vigente, sujeito à proveniência documentada |
| Apresentação ferroviária comparativa | `routes7_comparison_projection.py` e `dq32_macro_opportunities_model.py` | Vigente; ainda sujeito a consolidação arquitetural |
| Pesquisa ampliada DATA 9 | [DATA9_RAIL_GAPS_2026_11.md](research/DATA9_RAIL_GAPS_2026_11.md) | Snapshot histórico de 2026, não horários 2027 |
| Inventário 30×46 | [DATA9_1_COVERAGE_AUDIT_2026_11.md](research/DATA9_1_COVERAGE_AUDIT_2026_11.md) | Auditoria do snapshot 18/11/2026 |
| Retorno, fuso, conexões | `rail_temporal_contract.py`, `rail_transfer_contract.py`, `weekend_return_validation_model.py` | Contratos vigentes: data e horário devem ser comprovados |
| Acesso urbano e caminhada | `dq30_walking_access_model.py`, `data8_local_access_model.py` | Evidências distintas: documentada ≠ hipótese editorial |
| Validação automatizada | [validate.yml](../.github/workflows/validate.yml) | Workflow vigente, Python 3.11 |
| Segurança de publicação de planos | `public_plan_safety.py` e `private_continuity_store.py` | Separar repositório público de dados privados |

## Documentação histórica, preservar sem reescrever

| Documento | Interpretação correta |
|---|---|
| [AGENTS_COORDINATION.md](../AGENTS_COORDINATION.md) | Plano de três agentes de fase anterior; não é a lista atual de PRs abertos |
| [ARCH_STABILIZATION_PLAN.md](ARCH_STABILIZATION_PLAN.md) | Plano original de arquitetura; iniciativas implementadas parcialmente ou em fases posteriores |
| [DQ31_LOGISTICS_FIRST_AUDIT.md](DQ31_LOGISTICS_FIRST_AUDIT.md) | Evidências e decisões da fase DQ 3.1, não cálculo de viagem completa |
| [UX503_DESTINATION_LED_BASE_COMPARISON.md](UX503_DESTINATION_LED_BASE_COMPARISON.md) | Entrega da comparação por wishlist; consultar código para alterações posteriores |
| [ARCH14_PERFORMANCE_BASELINE.md](ARCH14_PERFORMANCE_BASELINE.md) | Microbenchmark de CI da época, não SLA de produção |
| [ARCH10B_DOCUMENTARY_EQUIVALENCE.md](ARCH10B_DOCUMENTARY_EQUIVALENCE.md) | Auditoria de paridade; não converter divergências documentais silenciosamente |
| Relatórios `RELATORIO_*`, prompts `PROMPT_*` | Registro histórico de decisões, não requisitos automaticamente vigentes |

## Semântica que não deve ser perdida

1. Tempo de **ida** não é ida/volta. O retorno necessita observação própria.
2. Deslocamento **local** não requer trem intermunicipal, mas o acesso urbano ainda pode ser desconhecido (`None` não vira zero).
3. Um mínimo publicado sem horário e estação na data não garante passeio.
4. Custos incompletos, ingresso desconhecido e visita externa têm escopos diferentes; ver DATA8.
5. `TripPlan` é o estado oficial; favoritos e comparações exploratórias são read-only até ação explícita.
6. Comparações multicritério somente se dados e cenários forem equivalentes. Cobertura documental não equivale a nota de qualidade ou viabilidade.
7. Dados em `data/user_plans/` requerem decisão separada de privacidade/retenção; não remover ou expor por ajustes documentais.

## Como validar

```bash
python -m compileall -q .
python tools/validate_research_data.py
python -m unittest discover -s tests -v
```

**Importante:** este índice é documental. Não introduz motor logístico, consolidação de dados de 2027, mudança de persistência, ranking automático ou exclusão de módulos.
