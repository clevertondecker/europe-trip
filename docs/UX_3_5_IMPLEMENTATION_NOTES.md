# UX 3.5 — Calendário inteligente (implementação)

## Onde encontrar

**Meu roteiro → Organizar viagem → Calendário inteligente**. As opções **Por período ou data** e **Calendário completo** continuam disponíveis.

## Regras do produto

- `smart_calendar_model.availability_matrix` deriva os dias do `TripPlan` atual via `calendar_model`; preserva Itália, instalação, férias restantes, trabalho remoto e fins de semana.
- `validate_calendar_preferences` não infere expediente brasileiro e aceita horários locais europeus somente quando o usuário os informa. **Não** agenda noites automaticamente sem horários/retornos de 2027.
- `suggest_calendar` devolve no máximo três rascunhos determinísticos para os locais escolhidos, respeitando a etapa e datas já aprovadas. Considera trabalho/instalação como indisponíveis para passeio longo e não transforma conexão não pesquisada em impossibilidade.
- Toda sugestão informa a razão e o que ainda precisa ser confirmado (retorno de transporte, última milha, abertura, ingressos, pernoite). A tarifa não é adicionada novamente à verba de passeios.
- `manual_calendar_move` permite datar, mover, repetir visita francesa em outra data e retirar a data sem excluir atrações. `calendar_visit_model` já descreve a regra de **uma passagem intermunicipal por visita**, não por atração.
- `review_calendar_change` valida `plan_id`, `revision`, base, etapa, datas, duplicações, atividades bloqueadas e que **todas as mudanças do JSON constam na revisão visível**. `apply_calendar_change` exige confirmação e atualiza `assignments` e/ou `flexible_visits` em **uma revisão canônica** via `change_plan`. Não há gravação remota nem reserva.
- A interface recupera subvisão, semana, etapa, filtro e propostas durante a sessão. Os links de orçamento e pesquisa retornam diretamente ao calendário. Exportação JSON de rascunho é opcional; ao importar, a proposta é revista na revisão atual.
- `TripPlan` schema v1, `planning_session`, o backend de autenticação, orçamento oficial e decisões do Drive permanecem intocados.

## Limitações verificáveis

- A viagem usa data de partida **proposta**, após 04/09/2027; nenhum horário ou preço de 2027 foi comprado ou cotado.
- Uma rota histórica com tempo de **ida** não comprova retorno viável; todas as propostas estão condicionadas.
- Para trajetos marcados como `overnight`, a versão 3.5 **não força um bate-volta**: apresenta pendência de bloco com pernoite e sugere pesquisa. A formalização de visitas com múltiplos dias exige mudança de schema com revisão separada.
- O calendário não produz economia monetária exata ao trocar uma data quando tarifas de ida/volta e ingressos equivalentes não estão documentados; `finance_delta_brl=None`.
- Não há sincronização privada automática entre dispositivos. Salvar o roteiro continua usando os controles da UX 3.2; a UX 3.6 abordará continuidade e persistência segura.
- UI validada por Streamlit AppTest, **não** por navegador real; acessibilidade/responsividade necessitam revisão de UX 3.9.

## Testes

`tests/test_ux35_smart_calendar.py` cobre: repartição de dias, bloqueio de trabalho e instalação, Itália isolada da França, datas já aprovadas, condicionalidade de retorno, rejeição de datas ocultas, revisão obsoleta, mudança manual sem perda de seleção, visita repetida e volta contextual do orçamento.

Executar `python -m compileall -q .` e `python -m unittest discover -s tests -v`. Validar também os contratos legados da UX 3.2–3.4 e os relatórios do GitHub Actions. Não publicar sem CI verde.
