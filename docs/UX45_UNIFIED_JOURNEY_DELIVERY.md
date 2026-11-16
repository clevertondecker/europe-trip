# UX 4.5 — Inventário e entrega de unificação de passeios

## Auditoria dos caminhos existentes

| Entrada | Antes | Autoridade | Depois |
|---|---|---|---|
| Meu roteiro → Meu planejamento (incluir/editar) | `upsert_flexible_choice` sem feedback estruturado | `packages` + `flexible_visits` no TripPlan; Itália só flexible | `commit_outing`: mesmo domínio, resultado `OutingResult` |
| Meu planejamento (remover) | `remove_flexible_choice` com confirmação | Remove pacote, metadados e assignments | `delete_outing(confirmed=True)` e comunica datas |
| Explorar → Passeios (diálogo) | `save_outing` sempre passava UNASSIGNED: **apagava períodos já escolhidos** | Guarda `can_edit`; bloqueia base hipotética | `commit_outing(period=None)` recupera período anterior, confirmação, feedback e link contextual |
| Explorar → Passeios (remover) | Removia no primeiro clique | `remove_flexible_choice` | Confirma impacto e usa `delete_outing`; modo simulação ainda bloqueado |
| Meu roteiro → Melhorar meu roteiro → Descobrir | **Quero visitar** aprovava atrações sugeridas imediatamente, sem revisão | `recommended_itineraries.approve_destination` → `accept_approved_plan` | Revisar atrações+período, confirmar, só então `commit_outing`; retorno preserva pesquisa |
| Meu roteiro → editor legado Meus passeios | `select_package`/`delete_package`, estados próprios | Plan canônico | Usa `commit_outing` e `delete_outing`; tela legada mantida |
| Simular roteiros | Propostas e boards imutáveis até aprovação | `scenario_board_ui` + `accept_approved_plan` | **Intocado**; continua exigindo revisão de proposta |
| Organizar datas | `assignments` e agendamento italiano específico | `schedule_package`, `schedule_italy_visit` | **Intocado**; flexível atualiza via contrato |
| Preferência Quero visitar | Interesse por atração, não passeio | `preferences` | **Intocado**; distinto de adicionar |
| Armazenar online | Ações explícitas de salvamento e opt-in | GCS/GitHub/backup existentes | **Intocado**, feedback diz sessão não salva remotamente |

## Contrato e efeitos
`ux45_outing_contract.py` implementa `preview_outing`, `apply_outing(confirmed=True)`, `remove_outing(confirmed=True)`, `OutingResult`. Não cria segundo estado; reutiliza `itinerary_flow_model.upsert_choice/remove_choice`. Duplicatas não são criadas; atualização sem mudanças não força revisão; período e datas anteriores são preservados. Itália mantém objetos de lua de mel distintos de pacotes franceses.

`planning_session.commit_outing/delete_outing` são a única fronteira Streamlit dos novos fluxos; proteção de simulação `explorer_mutation_guard.can_edit` continua antes do commit. As propostas financeiras/ferroviárias não foram tocadas.

## Continuidade
`ux45_navigation_context.handoff` captura apenas filtros efetivamente presentes do explorador ou descoberta, aponta para `Meu roteiro → Meu planejamento`, define etapa francesa e destaca a edição do destino. `return_to_origin` restaura filtros/cidade-base ao retornar, elimina handoff após uso e não altera o TripPlan. Navegação manual por abas descarta contexto antigo. Não cria novos deep-links nem páginas.

## Persistência
`_commit` ainda marca `advisor_local_changed`, preserva snapshots legados e não grava automaticamente na rede, exceto quando a configuração anterior de autosave explícito estiver habilitada. O resultado declara `session_only` porque persistência assíncrona não é garantia. Itália e propostas existentes ficam intactas.

## Limitação identificada para o exemplo de aceite
O catálogo de atrações `data/attractions_2027.json` **não inclui Bruxelas e Bruges como destinos editáveis**. DQ2.0/DQ2.1 dispõem de evidências sobre esses locais, mas elas não equivalem a atrações canônicas. Como a UX4.5 proíbe alterações de datasets e inclusão de atrações fictícias, a jornada é validada com **Colmar e Luxemburgo**. Cadastrar atrações reais de Bruxelas/Bruges, com fontes e IDs estáveis, exige uma mudança separada de catálogo, não esta refatoração. Não dizer que o exemplo Bruxelas → Bruges foi concluído.

## Testes e revisão
- `tests/test_ux45_outing_contract.py`: adição, edição sem duplicação, preservação de período+data, remoção explícita, Itália, simulação protegida e retorno de contexto.
- `tests/test_destination_discovery_ui.py`: sugestões exigem revisão antes de incluir e abrem o editor oficial.
- `tests/test_p0_explorer_isolation.py`: guard preservado e novos handlers confirmados.
- Suíte existente preserva backup, cenários e calendários.
- Rodar `python -m compileall -q .` e `python -m unittest discover -s tests -v` via CI.
- Browser real, mobile, modais e persistência com credenciais demandam teste visual/autenticado; AppTest não garante pixel-perfect.

## Escopo e governança
Sem mudanças em `assets/styles.css`, tokens, orçamento, dados ferroviários, cidades, reservas, GCS/Drive ou aprovação de propostas. PR isolado; merge/deploy somente após aprovação do usuário.

## Próximos incrementos
1. Acrescentar ao catálogo atrações verificadas em Bruxelas/Bruges sem nomes fictícios, seguindo modelo de dados;
2. Revisar visualmente continuidade do diálogo e o editor em 375/768/1280 px;
3. Avaliar desativação de editores legados depois de migração de usuários, mantendo compatibilidade de backups.
