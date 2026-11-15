# Changelog — auditoria e evolução do Nossa Europa 2027
Revisão: 15/11/2026 · Branch de execução: `audit/p0-finance-calendar-safety-2027`

## Correções implementadas — prioridade integridade

- **Normalização EUR/CHF em rankings:** cria `money_units.py` e altera
  `destination_recommender.py` para trabalhar com EUR equivalente,
  usando câmbio EUR/BRL e CHF/BRL explícito. Taxas correntes propagadas
  a `discovery_ui.py` e `travel_profile_scenarios.py`.
  Mantém separadamente o valor original em EUR/CHF na tela.
- **Economias em ajustes do orçamento:** `unified_budget.scenario_total`
  passa a aceitar deltas finitos negativos, mas rejeita qualquer nova
  despesa ou total final menor que zero. A interface em `app.py` aceita
  economias com limites associados à verba de cada categoria.
- **Calendário:** cria `calendar_assignment_validation.py`, usado
  em `planning_store.change_plan` e `trip_plan_model.apply_proposal`
  para impedir novas excursões de dia inteiro em dias de trabalho,
  instalação, Itália ou fora do horizonte. Mantém datas antigas
  aprovadas sem exigir migração nem editar backups.
- **Propostas:** otimização não pode alterar uma data já confirmada
  nem aplicar proposta de outro plano (quando `plan_id` consta).
- **Proteção de salvamento público:** `public_plan_safety.py` recusa
  campos inesperados e endereços de e-mail antes do PUT no GitHub.
  Permanece necessário o aceite e login existentes; isso **não** torna
  o armazenamento público confidencial nem apaga históricos.
- **Testes:** novos cenários para erros de câmbio, economia válida e
  excessiva, conflito de calendário, proposta rejeitada e conteúdo de
  plano com dados pessoais.

## Compatibilidade
`TripPlan.schema_version=1` preservado. Nenhuma mudança de nome de
atributos salvos, nenhuma migração automática. Nenhum dado pessoal,
itinerário aprovado, orçamento oficial ou infraestrutura de produção
foi alterado remotamente. Sem reservas, compras ou gravações no Drive.

## Arquivos de auditoria
- `docs/AUDITORIA_TECNICA.md`
- `docs/AUDITORIA_ROTEIRO_2027.md`
- `docs/PENDENCIAS_DADOS_2027.md`
- `docs/CHANGELOG_EVOLUCAO.md`

## Testes e integração
Executar `python -m unittest discover -s tests -v` via GitHub Actions,
além de checks de compilação e inicialização Streamlit quando disponíveis.
Registrar resultados no PR; merge somente com CI aprovado.

## Limitações e próximos passos
- Repositório público com JSON de planos: precisa estratégia de
  armazenamento privado, autorização/retensão e migração aprovada.
- Motor monetário usa `float`/arredondamentos em outros caminhos;
  padronização total de `Decimal` segue pendente.
- `app.py` tem múltiplas responsabilidades; refatoração incremental
  planejada, não executada integralmente aqui.
- Pesquisa de custos/tempos 2027 e comparação real de aluguéis mobiliados
  permanecem incompletas. Não há vencedor entre as cidades-base.
