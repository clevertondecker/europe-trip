# UX87 — Comparação perceptível e investigação contextual | PR #203

> **Status:** especificação para implementação futura. UX88 (#204) está absorvido. Implementar **somente após #201 integrado à main**, consumindo `CHOICE` sem outro seletor. Nenhuma alteração funcional existe ainda nesta branch.

## Objetivo
Atue como Staff Streamlit Engineer, Principal Product Designer, Accessibility Reviewer e Finance UX Engineer. Em **Explorar > Comparar bases**, duas cidades selecionadas devem gerar imediatamente uma **resposta útil e visível**, seguida da matriz, sem outra confirmação, novo modo ou outro conjunto de destinos. Com uma cidade, o usuário pode conhecer perfil, mapa ou custo sem comparar.

## Contratos do HEAD a auditar antes de codificar
- #201 entrega uma única seleção `rec03b_handoffs.CHOICE`, escopo confirmado `rec03a_scope` e cartões deduplicados. Enquanto #203 não estiver integrado, usa **uma CTA transitória** que envia a mesma seleção a UX503 por `queue_handoff(kind="manual")`.
- UX503 já possui `compare_wishlist_bases(... visible_destination_ids=...)` e `decorate_comparison`; verificar resultados, catálogo e compatibilidade de evidência com REC02 antes de adaptar uma projeção **somente leitura**. Células `historical`, `reference_only`, `local`, `no_time` mantêm semântica própria.
- `rec03b_handoffs` valida escopo, identidade/contexto, PREVIOUS, MANUAL_KEYS e caminhos profile/map/planning. REC04 mantém `request_simulation`, `apply_simulation_request`, `valid_context` e `return_to_source`. `rec04_candidate_capabilities.capability_for` distingue capacidades.
- `ux64_navigation_model` preserva três áreas públicas; `TripPlan` continua oficial. Auditar as versões após #201 — não assumir que as funções continuaram idênticas.

## P1 — A comparação aparece e é percebida
1. **0 bases:** apresentar candidatas e nenhuma matriz vazia. **1 base:** resumir que é possível investigar individualmente e que outra pode ser selecionada para comparar. **2–5 bases:** calcular projeção read-only no rerun e **mostrar comparação na própria atividade imediatamente**. Remover a CTA transitória `Comparar N cidades` do #201; não exigir outra seleção, clique, aba, troca `MANUAL/SUGGESTED` ou página.
2. **Localização recomendada:** uma **região compacta de comparação** logo após o resumo das bases selecionadas, **antes da lista completa de cidades**. A região mostra "Comparando Mulhouse e Colmar", estado da evidência e 2–3 conclusões verificáveis. A matriz detalhada vem na mesma atividade abaixo dessa região, com link/âncora contextual acessível `Ver detalhes da comparação`.
3. Se o usuário estiver navegando nas candidatas mais abaixo, o controle selecionado deve mostrar imediatamente feedback textual não intrusivo (ex.: `2 cidades selecionadas — comparação disponível`) e acesso curto à região de comparação. Não usar `st.toast` como único retorno, rolagem forçada, `st.rerun` em loop, overlay global ou novo estado persistente. Manter escolhas atuais visíveis e editáveis no resumo.
4. **Selecionar/desmarcar** atualiza apenas `CHOICE` e a projeção visual. Não mover automaticamente o usuário para uma segunda interface nem atualizar filtros do UX503 legado. Preserve o acesso manual avançado e `PREVIOUS/MANUAL_KEYS` sem sincronização desnecessária.
5. **Escolha justificada:** região compacta + atalho contextual, em vez de rolagem forçada (intrusiva), botão "Comparar" (confirmação redundante), ou matriz só no rodapé de uma lista longa (pouco perceptível). Em 390 px, posicionar o resumo acima da lista longa e dar feedback junto ao controle; link para detalhes é opcional e não condiciona o cálculo.

## P2 — Uma resposta compreensível vem antes da matriz
O resumo comparativo precisa responder, **com dados existentes**:
- Quantos destinos do escopo possuem tempos **históricos** ou **indicativos** para cada base, separados de trechos `local` e `no_time`.
- Quais destinos `must_visit` ainda têm lacunas importantes por base, com nomes quando sustentados pela projeção.
- Se as cidades compartilham um **conjunto de trajetos comparável** (completo, condicional com destinos omitidos, ou insuficiente); explicar diferenças sem pontuar globalmente.
- O que não se sabe: horários 2027, retorno, frequência, última milha, alugueis reais, custos comparáveis.

Se faltar evidência, exibir: **"Ainda não temos evidências suficientes para comparar essas cidades de forma conclusiva."** e indicar pesquisas pendentes REC05 sem estimar trajetos inexistentes. Nunca converter `no_time` em zero, somar mínimo de ida como viagem completa ou usar cobertura documental para afirmar "melhor logística".

## P2 — Matriz acessível e fontes relevantes
1. Matriz sob o resumo: **destinos confirmados × bases `CHOICE`**, com prioridades da wishlist e texto por célula (`histórico: 20 min`, `referência indicativa: 1h15`, `local: confirmar acesso`, `sem tempo pesquisado`) somente quando suportado por dados canônicos. Não usar emojis/cores como único significado.
2. `reconcile_session_scope` deve estar `ready`; consumir exatamente `scope["destination_ids"]`. Em `scope_required`/identity mismatch, suspender resumo e matriz, mostrando a revisão de escopo já prevista no #201. Não utilizar subconjunto padrão do UX503 manual sem avisar.
3. Distinguir categorias REC02 e UX503 que **não** sejam equivalentes. Fazer adaptação de apresentação pura, não reimplementar `compare_wishlist_bases`, `build_wishlist_matrix`, `evaluate_matrix` ou cálculos de ponderação.
4. Mostrar referência mínima e ressalva junto à célula; links, datas, observações conflitantes, condições ferroviárias, REC05 e métodos ficam em detalhe sob demanda. Renderizar detalhes pesados somente quando abertos, sem ocultar informação que muda interpretação do resultado.
5. Desktop: matriz com leitura cruzada; tablet/mobile: cards por destino ou scroll **interno** com rótulos fixos/legíveis. Nunca criar overflow horizontal da página, cortar BRL/tempos, ou omitir texto acessível.

## P2 — Ações e finanças proporcionais às capacidades
1. Perfil, mapa e `Simular custo` são ações contextuais de **uma cidade**, na seção selecionada/detalhe; não repetir 3 botões grandes em todo cartão e novamente no rodapé. **Não exigir duas bases** para abrir uma simulação.
2. Perfil/mapa: usar REC03B `queue_handoff/apply_handoff`; simular: usar REC04 `request_simulation/apply_simulation_request`, com clique explícito, escopo/conta/plano/cidade validados e retorno correto.
3. Usar `capability_for(city)` e comunicar separadamente:
   - `scenario_selectable`: **simulação hipotética**, não cotação local;
   - `detailed_budget_supported`: **detalhamento financeiro disponível**, ainda sujeito a fontes e lacunas;
   - `official_plan_supported`: **elegibilidade técnica para base oficial**, sem seleção automática;
   - `rental_quote_2027_available`: se falso, **aluguel/caução 2027 não cotados**, nunca exibir preço local conhecido ou R$0.
4. Sem `scenario_selectable`, não oferecer CTA ativa ou valor fabricado. Se houver apenas simulação geral, explicar o limite **antes de abrir** Orçamento; não etiquetar valores de referência como preços reais ou "economia".
5. Manter `unified_scenario`, `unified_style`, `budget_cap_confirm`, `scenario_base_selected`, `ux_mode`, `unified_override_rent`, bases oficiais, teto e cenários 60k/70k. Navegação/simulação não muda orçamento ou base oficiais.

## Continuidade sem prender o usuário
- `CHOICE` é a única seleção de cidades; `rec03a_scope` o único conjunto confirmado de destinos. Retorno de mapa/perfil/Orçamento preserva contexto **enquanto válido na sessão**; mudança de identidade/plano/wishlist invalida e exige revisão. Não prometer recuperação entre sessões.
- O usuário pode descobrir/incluir destinos, montar e salvar roteiro **sem datas e sem base definitiva**, sair para orçamento ou voltar ao roteiro a qualquer momento. Não exigir "concluir comparação".
- Preservar handoff planejamento, a comparação manual legada e recuperação de filtros. Remover do caminho principal apenas o encaminhamento redundante que #201 usou temporariamente.

## Testes de aceite (bloqueantes após implementação)
| Cenário | Comportamento esperado |
|---|---|
| `CHOICE` com 0 ou 1 base | Sem matriz vazia; uma cidade permite perfil/mapa/simulação se suportada |
| 2 bases | Resumo comparativo visível próximo à seleção e matriz disponível **sem clique extra** |
| 3, 4 ou 5 bases | Atualização na mesma atividade, sem truncamento e sem segunda lista de seleção |
| Muitas cidades no catálogo | Feedback junto ao card e acesso curto à comparação, sem rolagem forçada |
| Escopo `ready` vs alterado | Sem confirmação repetida quando válido; em `scope_required` sem resultados antigos |
| Evidência histórica/indicativa/local/ausente | Contagens e células coerentes, sem rank artificial ou soma de deslocamentos incompatíveis |
| Dados insuficientes | Mensagem explícita de inconclusão e lacunas REC05 |
| Simulação genérica | Explica que é hipotética e que aluguel 2027 não foi cotado |
| Capacidade detalhada / base oficial | Distingue flags sem oficializar ou inventar preço |
| Retorno perfil/mapa/orçamento | Seleção válida restaurada; documento/identidade divergente invalida |
| Roteiro | Pode incluir e salvar sem datas ou decisão de base |
| 1440 / 768 / 390 px | Sem overflow de página, duplicação de CTA, perda de foco/teclado |

Executar `python -m compileall -q .`, `python -m unittest discover -s tests -v`, AppTests de navegação e invariantes, CI no HEAD. Validar visualmente em navegador real (incluindo hover, focus, disabled, contraste WCAG AA) ou declarar **pendente**. Comparar os passos reais antes/depois sem inventar indicadores de usabilidade.

## Entrega e restrições
Implementar **somente na branch existente do #203**, após #201 implementado e integrado. Código de apresentação, orquestração e testes apenas; sem novos modelos persistentes, novos pesos, alterações de REC01/REC02/UX64, nem Design System paralelo. Não fazer merge automático. **CI de documentação não equivale a implementação concluída.**
