# Nossa Europa 2027 — UX 5.0.1 / Descoberta sem cidade-base

**Escopo implementado:** somente o primeiro PR do roadmap UX 5.0. A seleção persistente e qualificada (UX 5.0.2), a matriz dos destinos desejados × cidades-base (UX 5.0.3) e a navegação guiada (UX 5.0.4) **não foram implementadas**.

## Diagnóstico do fluxo atual

A navegação possui `Explorar → Cidades-base / Comparar / Passeios / Mapa`, enquanto `attractions_ui.render_explorer()` inicia a investigação pedindo uma cidade-base. Isso permite pesquisar passeios, mas impõe uma escolha antes de descobrir as cidades que queremos conhecer. O TripPlan oficial já conserva `base_city` separado dos seletores exploratórios; a experiência precisa preservar essa distinção. As 30 cidades-base e as 14 cidades do catálogo canônico não são a mesma contagem de destinos turísticos.

## Mapa de reuso e fronteiras

| Recurso existente | Reuso na UX 5.0.1 |
|---|---|
| `attractions_model.load_attractions()` | 14 destinos e 65 atrações do catálogo operacional, com fontes e fotos licenciadas quando cadastradas |
| `dq32_macro_opportunities_model.load_macro_tourism()` | 30 registros de pesquisa local, sem afirmar que são 30 atrações novas e distintas |
| `dq32_macro_opportunities_model._registry()` | União por IDs canônicos dos destinos existentes, pesquisas exploratórias e 30 cidades-base |
| `dq32_macro_opportunities_model.reconcile_attractions()` | Reconciliar atrações semanticamente equivalentes sem apagar IDs de origem, incluindo Casamatas do Bock |
| `base_explorer_model.load_exploration()` | Destinos existentes sem exigir que haja trem pesquisado |
| `base_research_expanded_model.load_research()` | Cidades de pesquisa sem afirmar deslocamento viável |
| `planning_session.active_plan()` | O TripPlan continua autoridade; **sem mutações neste PR** |
| `ux41_favorites_model` | Favoritos existentes são de cidades-base, não destinos desejados; não reutilizados como interesses turísticos |
| `ux_navigation.py` | A rota `Explorar → Passeios` continua intacta, sem segundo sistema de navegação |

## Experiência entregue

A página `Explorar → Passeios` começa pela seção **O que gostaríamos de conhecer?**, antes da pesquisa opcional de passeios por base. Permite busca textual por destino/atração, filtro por país, filtro por categoria e visualização de cartões de cidade com atrações, fontes, status de pesquisa e fotografias existentes com créditos. Exibe destinos sem atrações individuais documentadas, sem penalizá-los.

A seleção **Tenho interesse** é uma cesta **transitória nesta sessão do Streamlit**; não modifica `advisor_plan`, `mandatory_destinations`, `preferences`, `ux41_favorites`, arquivo de plano, nuvem ou banco. Não há promessa de persistência/reabertura nesta etapa. O UX 5.0.2 deverá projetar essas intenções nos contratos já existentes ou apresentar alteração versionada mínima, **sem** criar uma fonte paralela. A UX 5.0.3 utilizará a cesta escolhida para comparar 2–5 cidades-base pela **mesma lista de destinos**, distinguindo evidências observadas de lacunas.

O TripPlan mantém a cidade-base atual como referência provisória. A descoberta não altera a cidade-base nem reserva, confirma retorno ferroviário, transforma um candidato em passeio agendado ou inventa tarifa para 2027.

## Dependências e riscos

- **UX 5.0.2** depende do catálogo estável e dos IDs normalizados do 5.0.1, e terá de resolver persistência, classificação de interesse e compatibilidade com backup.
- **UX 5.0.3** depende da lista classificada e reaproveitará `evidence_query_model.get_rail_evidence()` sem confundir mínimo histórico, típico, conexão de volta e última milha. Deve apresentar 2–5 bases e todos os mesmos destinos, sem ranking artificial.
- **UX 5.0.4** depende das três experiências anteriores; a navegação atual permanece funcional até que haja AppTests de migração.

Riscos: fotos remotas podem estar indisponíveis; dados heterogêneos não provam passeios; escolhas transitórias não devem ser apresentadas como salvas; filtros e paginação não devem apagar interesses; a sessão oficial não deve sofrer writes. Validações incluem deduplicação de Luxemburgo, 30+ destinos, filtros e testes AppTest com cinco destinos de interesse e alternância de base apenas na seção antiga.

## Critérios de aceite

- Descoberta independente da base, com destinos/atrações existentes e fontes rastreáveis.
- Cidades sem horários/atrações aprofundadas não desaparecem.
- Identidade canônica e IDs originais preservados.
- Nenhuma confirmação de passeio, reserva ou transporte.
- TripPlan, orçamento e backups inalterados.
- Testes unitários e AppTest aprovados.
- Sem merge ou deploy até revisão.
