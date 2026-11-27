# UX132C3 — Consolidação da cobertura e clareza das sugestões

Atue como Staff Software Engineer e Principal Product Designer. Dependência: #272 UX132C2 (HEAD 9eeb9c8); antes de integrar, sincronizar eventuais correções do #272, retarget para main e confirmar diff exclusivo. Não alterar datasets, contratos DATA24, orçamento, recomendação REC02 ou o TripPlan.

## Objetivo
Reduzir hierarquia e esforço para encontrar lacunas e entender a diferença entre sugestões automáticas e cidades escolhidas. Cobertura agora tem três domínios, não apenas transporte. Mover a entrada para Explorar → Cobertura dos dados, como tarefa pública no roteador canônico existente; manter Comparar bases com apenas Explorar alternativas e Minha comparação. Não criar nova área principal ou duplicar renderização. Migrar sessão antiga que estava na cobertura uma única vez, preservar os estados de domínio e filtros, comparação, DRAFT, SCOPE, CHOICE, wishlist, TripPlan, orçamento, persistência, handoffs e links legados. Deselect é no-op. Acesso à cobertura sem wishlist/escopo e sem chamar recomendação. Voltar à comparação restaura sua seleção/modo, sem alterar plano.
## Sugestões
- Cabeçalho acima dos cartões distingue sugestões automáticas do catálogo completo e da seleção manual. Explicar que destaques REC02 usam mínimos de ida em conjuntos comparáveis e fronteira documental; não ranking global ou recomendação de preço, retorno, frequência, moradia/custo de vida ou trabalho remoto. Não promover falta de dados a desvantagem logística.
- Expor seleção/contador e ação de comparar antes da galeria, sem segundo seletor ou toolbar duplicada. Manter feedback local nos cartões. Distinguir destaque por menor mínimo ponderado do mesmo conjunto de alternativa com evidência parcial, usando highlight_kind/reasons existentes, sem inventar ordenação.
- Corrigir descrições que prometem comparar custos não utilizados nas sugestões; preservar comparação financeira oficial e ações existentes.
## Cobertura
- Composição única com visão geral e áreas especializadas; resumo ferroviário explícito, atrações com indicadores essenciais compactos, estados de ingresso separados, morar/trabalhar distingue requisitos futuros de referências históricas. Denominadores reais, N/A, sem nota geral, detalhes e fontes na área correspondente. Sem novo motor, cache ou novas métricas artificiais. Preservar filtros por domínio e estado do usuário.
## Aceite
Testar rota canônica, migração, ausência de entrada duplicada, acesso sem wishlist, alternância por tarefa pública, recuperação de seleção, navegação com escopo em edição, handoffs, seleção manual, ausência de novas escritas e isolamento de projeções. Adaptar testes de UX132A/B/C1/C2 à nova entrada sem remover regressões. QA desktop/mobile se disponível; CI final e auditoria versionada obrigatórias. Manter draft. DATA26 e recomendação multidimensional ficam fora do escopo.


## Registro da implementação
- A rota canônica Explorar/Cobertura dos dados passa a ter página própria, sem dependência do escopo. Mantém três áreas principais, cinco atividades em Explorar e dois modos em Comparar bases. Remove a entrada aninhada. Migração do modo antigo ocorre antes de montar widgets, sem alterar dados do plano; pedido explícito de comparação tem precedência.
- A seleção manual permanece CHOICE e o toolbar existente foi movido para antes da galeria, sem duplicação. Cabeçalho das sugestões identifica o critério REC02; destaques completos e documentais são diferenciados, sem afirmar ranking ou considerar custos que o motor não usa. Busca e catálogo integral permanecem disponíveis.
- A visão geral usa os mesmos indicadores canônicos; atrações apresentam barras compactas com razões e três estados de ingresso. Morar e trabalhar preserva requisitos de decisão separados dos históricos. Não há alteração em datasets, motor REC02, contratos DATA24 ou orçamento.
- Testes novos de rota, migração, seleção automática versus manual, retorno e preservação de estado; regressões de UX132A/B/C1/C2 adaptadas à tarefa pública e mantidas. A busca de código do conector não retornou referências adicionais; suite completa deve confirmar compatibilidade com demais testes do repositório.
- Dependência #272 ainda pendente durante a implementação. PR deve ser retargetado para main após sua integração; se HEAD da dependência mudar, revisar e sincronizar antes de validar o diff. CI final e QA visual desktop/mobile ainda não executados/confirmados. Não mergear sem autorização.


## Review final — estabilização
- P1 confirmado: route/from_legacy/SECTIONS já reconheciam Cobertura dos dados, mas LEGACY_PAGES não. Registro corrigido; consumidor real app.py usa a lista no radio legado. Teste adicional de todos os destinos canônicos, sem alteração dos testes anteriores.
- P2 confirmado: remember gravava None no shadow e o próximo rerun retornava ao default. Helper opt-in navigation_widget_state preserva a última opção válida somente para ux112_active_view, ux132_domain e ux132_coverage_section. Widgets de entrada genéricos mantêm o comportamento original.
- Migração: normalização em apply() é única; set_task e set_from_legacy sinalizam intenção explícita e a recuperação de pedido legado alterado também tem precedência. Removida duplicação em select_public_task. Nenhuma nova rota, abstração ou persistência.
- REC02 permanece intacto. Explicação por complete_reference_group, individual_complete, local_investigation e conditional_investigation, com motivo de menor mínimo no subconjunto apenas quando registrado em reasons. Sem ranking, pesos ou métricas novos.
- Testes: registro canônico, precedência explícita e migração, quatro tipos de destaque, AppTest.from_file(app.py) para acesso, deselect dos três controles, retorno, filtros, ausência do motor na cobertura, uma única renderização e estado existente. Regressões anteriores de DRAFT/SCOPE/CHOICE e handoffs mantidas.
- #272 integrado em main (4cc9d91; CI 45998248928: 1454 executados, 2 ignorados, sem falhas). #273 retargetado para main; merge base é exatamente o HEAD 9eeb9c8 da dependência já incorporada. Diff exclusivo do UX132C3; sem mudanças de datasets/auditoria ou motor. CI do HEAD final pendente; AppTest real incluído mas execução ainda não confirmada. QA visual desktop/mobile não realizado. Autorização posterior do usuário permite merge somente após CI verde e ausência de conflitos/bloqueios, sem ignorar checks.

## Validação e ajuste das expectativas legadas
- CI 46000461732 (HEAD 1ce64ce): 1463 testes executados, 1459 aprovados, 2 ignorados e 2 falhas. Ambas as falhas são expectativas de navegação anteriores ao UX132C3: 13 seções internas em test_ux31_base_decisions e quatro tarefas de Explorar em test_ux82_shared_explorer_visual.
- Atualizadas as expectativas exatas para 14 seções e cinco tarefas, com asserções explícitas da nova rota, registro canônico e composição de Explorar. Nenhum teste removido, ignorado ou flexibilizado; as demais verificações de ausência de segundo roteador/persistência permanecem.
- A suite anterior confirmou paridade DATA24 e os novos cenários AppTest de navegação; a suite do novo HEAD ainda precisa passar antes do merge. QA visual não realizado.
