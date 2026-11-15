# Coordenação de 3 agentes — Nossa Europa 2027

**Orquestração:** agente integrador (único autorizado a editar arquivos compartilhados). **Estado:** tarefas planejadas; a criação de issues/branches não inicia execução automática de agentes.

## Protocolo obrigatório
1. Cada agente trabalha **exclusivamente em sua branch**, abre PR para `main`, e publica comentários nas issues GitHub de coordenação, informando decisões de API, dependências, alterações, testes e bloqueios.
2. Antes de codar, ler este documento, os relatórios atuais, o código real do repositório e as issues dos demais agentes. Ao final, notificar os outros dois por comentário na issue de coordenação contendo caminhos de módulos, assinaturas públicas e exemplos de retornos.
3. **Nenhum agente edita `app.py`, `travel_advisor_ui.py`, `discovery_ui.py`, `scenario_board_ui.py`, `planning_session.py`, `planning_store.py`, `trip_plan_model.py`, `advisor_finance.py`, `unified_budget.py`, `attractions_model.py`, `requirements.txt`, `README.md` ou `.github/workflows/validate.yml`. Estes arquivos são propriedade exclusiva do agente integrador.
4. Se precisar alterar um arquivo compartilhado, propor patch/assinatura em comentário na issue e deixar implementação da alteração para o integrador. Não realizar cherry-pick ou merge no `main` de forma independente.
5. Não sobrescrever planos versionados existentes, não alterar arquivos de Drive, OAuth ou Secrets, e não introduzir preços inexistentes ou supostamente válidos para 2027.
6. Todos os módulos novos devem ser **puros ou minimamente acoplados**, com funções chamadas sob demanda; persistência e mudanças do plano somente após consentimento. PRs devem trazer testes unitários e documentação dos contratos no próprio PR.
7. Integração na sequência: Agent 1 (métricas), Agent 2 (evidência de custos), Agent 3 (rascunhos/calendário/UX); o integrador adaptará as interfaces e executará a suíte completa entre merges.

## Ownership sem sobreposição
| Agente | Branch | Arquivos exclusivos |
|---|---|---|
| 1 Financeiro | `agents/finance-margins` | `finance_margin_metrics.py`, `finance_margin_ui.py`, `tests/test_finance_margin_metrics.py`, `docs/AGENT_1_FINANCE.md` |
| 2 Dados | `agents/outing-cost-data` | `outing_cost_evidence.py`, `data/outing_cost_evidence_2027.json`, `tests/test_outing_cost_evidence.py`, `docs/AGENT_2_COSTS.md` |
| 3 Experiência | `agents/draft-calendar-ux` | `draft_plan_store.py`, `calendar_visit_model.py`, `draft_controls_ui.py`, `tests/test_draft_plan_store.py`, `tests/test_calendar_visit_model.py`, `docs/AGENT_3_UX.md` |
| Integrador | `main` (somente após PR revisado) | Todos os arquivos compartilhados, integração final, CI, documentação agregada |

## Interfaces contratuais (propostas)
- **Agent 1:** `calculate_excursion_margin(finance_projection:dict, known_costs:dict, eur_fx:float, chf_fx:float, missing:list[str])->dict` retorna `allowance_brl`, `known_spend_brl`, `covered_known_brl`, `known_allowance_remaining_brl`, `known_overage_brl`, `budget_margin_brl`, `pending_count`, `coverage_caveat`, e `utilization_pct`. O nome 'saldo' nunca significa dinheiro livre garantido.
- **Agent 2:** `load_outing_evidence()->dict`; `evidence_for_outing(destination_id, attraction_ids)->dict` retorna itens com `category`, `amount` ou null, `currency`, `unit`, `status`, `source_url`, `verified_at`, `validity_period`, `confidence`; sem substituir preços existentes sem prova.
- **Agent 3:** `get_draft(plan_id, profile, store)->dict|None`, `save_draft(...)->...`, `list_drafts(...)->...` (adaptável ao backend escolhido pelo integrador); `validate_repeat_visits(plan, visits)->list` sem aceitar sobreposição e sem duplicar trem para múltiplas atrações na mesma visita. Nenhuma edição em arquivo JSON dos planos existentes sem migração autorizada.

## Critérios do integrador
- Nenhum PR mergeado sem revisão de diffs, testes, checagem dos limites de ownership e compatibilidade.
- Validação financeira: R$60k/70k, conversão EUR/CHF, provisão já reservada, margem global vs. saldo de excursões.
- Dados: ausência de cotação != zero; fonte real e data; pesquisas não validadas ficam como desconhecidas.
- Drafts: isolados do plano aprovado; recuperação, concorrência e alterações em outro navegador devidamente tratadas; nada salvo em repositório público sem consentimento.
- UI: AppTest + inspeção visual real quando possível.
