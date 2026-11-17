# UX 5.0.4 — Auditoria de rotas e jornada guiada

## Mapa atual (antes do ajuste)
| Área | Chave estável | Rota legada | Acesso |
|---|---|---|---|
| Minha viagem | Resumo | Visão geral | Página inicial, continuidade, indicadores, mapa e orçamento |
| Explorar | Passeios | Roteiro → Guias e pesquisas → Explorar atrações | UX 5.0.1 e 5.0.2, alternância via `ux502_view` |
| Explorar | Comparar | Comparar cidades | UX 5.0.3 e ferramenta anterior recolhida |
| Explorar | Cidades-base | Roteiro → Explorar bases | Pesquisas históricas e ferramentas avançadas |
| Explorar | Mapa | Mapa & destinos | Mapa legado preservado |
| Meu roteiro | Meu planejamento | Roteiro → Visão geral | `render_itinerary_workbench` |
| Meu roteiro | Organizar viagem | Roteiro → Visão geral / Calendário | `render_itinerary_workbench`, calendário inteligente |
| Orçamento | Resumo financeiro | Orçamento | Dados e cálculos existentes |

A chave `ux_section` é um widget do Streamlit montado em `app.py`, após o sidebar `ux_area`. `ux_navigation.bootstrap/apply/set_task/set_from_legacy` é o adaptador autorizado. `ux502_view` é outro widget montado sob Explorar/Passeios, com valores `Descobrir lugares` e `Minha lista`. A UX 5.0.3 usa `ux503_bases` só em sessão e retorna via `ux503_pending_return_to_wishlist`.

## Contratos e riscos
- Autoridade dos desejos: `ux502_interests` (schema v1 e importação privada), nunca um duplicado em etapas.
- Autoridade de roteiro: `advisor_plan` via `active_plan()`: `packages`, `flexible_visits`, `assignments`. `budget_scenario` é simulação, não confirmação de preços.
- Não há sinal persistido de "comparação concluída" nem de "base aprovada"; nenhum progresso ou confirmação será inferido da visita à tela ou de `base_city`.
- Navegação não deve criar writes: `_ux504_navigation_request` é apenas um comando efêmero; `app.py` o aplica antes de montar qualquer widget usando `set_ux_task` e `ux502_view`. Não altera TripPlan, revisão, backups ou opções de simulação.
- O callback de navegação executado após montagem do sidebar **não** deve modificar `ux_area` ou `ux_section` diretamente. Apenas enfileira a intenção para próximo rerun.
- Labels de `ux_section` podem mudar via `format_func` mantendo os identificadores estáveis. Rotas antigas, deep-links e mapa permanecem.

## Mudança mínima proposta
1. Novo modelo puro `ux504_guided_journey_model.py` com projeção (sem I/O) dos cinco passos e próxima ação conservadora.
2. `ux504_guided_journey_ui.py` exibe no topo de `Minha viagem → Resumo` título, subtítulo, cinco passos e uma ação contextual. Informações técnicas antigas continuam abaixo.
3. Chamada de aplicação do pedido de navegação após `bootstrap_ux` e antes dos widgets, com adaptador `set_ux_task`.
4. Mostrar rótulos legíveis nas tarefas da área Explorar; manter `Passeios`, `Comparar`, `Cidades-base` e `Mapa` como chaves/roteamento originais.
5. Ações contextuais para transitar entre descoberta, lista, comparação, roteiro, datas e orçamento, sem novas APIs de persistência.

## Validação
Testes unitários de projeção e intenção de navegação, AppTest com vazio/desejos/passeios/datas, round-trip e isolamento do TripPlan. Teste visual real somente se um browser/ambiente gráfico estiver acessível; em caso contrário não declarar validado.


## Refinamentos pós-revisão do HEAD 02236d69
- Com destinos desejados e nenhum passeio no roteiro, a página oferece **Comparar cidades-base** e **Começar a montar roteiro** simultaneamente; não inventa estado de comparação concluída nem obriga a escolher uma base antes de planejar.
- Estado do roteiro por **ID de destino**: união de destinos com pacotes e visitas flexíveis; destinos organizados têm ao menos uma data atribuída ou período flexível diferente de `Ainda não definido`. Múltiplas datas no mesmo destino contam uma vez para a classificação; uma indicação de período não vira uma data confirmada. Etapas pendentes continuam explícitas.
- Os painéis da página inicial anterior são preservados num único expander **Painéis anteriores, mapa, fontes e detalhes · avançado**, mantendo detalhes técnicos disponíveis sem disputar a atenção com as cinco etapas.
- A seleção temporária de bases e destinos visíveis da UX 5.0.3 passa a ter uma sombra **somente de sessão** para sobreviver à remoção automática de chaves de widgets do Streamlit entre rotas; o documento da UX 5.0.2 e o TripPlan não são modificados. O filtro de descoberta também é preservado ao usar a ação contextual.
- AppTests incluem navegação ponta a ponta, mudanças de bases, preservação dos filtros e da lista, além de verificação de ausência de mutação do plano ou solicitação de autosave.
