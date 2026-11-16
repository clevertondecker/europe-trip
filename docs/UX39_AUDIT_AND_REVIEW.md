# UX 3.9 · Auditoria técnica de jornadas e qualidade da interface

**Data:** 16/11/2026 · **Base:** `main` após PR #52 (UX 3.8) · **Estado:** auditoria por leitura de código e AppTest; navegador real não disponível neste ambiente.

## Inventário verificado (4 áreas, sem novas abas)

| Área | Código verificado | Jornada |
|---|---|---|
| Minha viagem | `app.py`, `planning_context_ui.py`, `continuity_ui.py`, `ux37_next_actions_ui.py` | continuar, revisar, salvar |
| Explorar | `city_decision_ui.py`, `base_change_model.py`, `private_city_studies_ui.py` | comparar bases, fontes, guardar estudo |
| Meu roteiro | `itinerary_flow_ui.py`, `smart_calendar_ui.py`, `planning_context_ui.py` | escolher, organizar, voltar e salvar |
| Orçamento | `budget_sections_ui.py`, `quote_research_ui.py`, `unified_budget.py` | simular, cadastrar cotação, retornar ao planejamento |

### Auditoria A — Produto / engenharia

**P1 · Troca de cotação pode reaproveitar campos do item anterior.** `quote_research_ui._edit_form` usa chaves de widget `ux38_edit_*` compartilhadas entre *todas* as cotações. Ao selecionar uma diferente, o valor inicial do widget pode prevalecer em relação ao conteúdo do novo item. Corrigir com namespace estável por ID, sem reescrever o modelo de cotações.

**P1 · Cotações não aparecem no Resumo antes de passar por Detalhamento.** `render_quotes_summary` lê somente `st.session_state["ux38_quotes"]`, enquanto a ação de leitura GCS fica exclusivamente no `render_quotes_details`. Melhorar com botão de carregar na própria área de resumo; manter busca sob demanda, sem escrita ou chamadas repetidas automáticas.

**P1/P2 · Entrada de cidade em linguagem técnica.** `quote_research_ui._edit_form` pede `Cidade/destino (ID, opcional)`, exigindo identificador interno. Trocar por seletor de lugares já reconhecidos, com fallback para dados legados (não remover IDs antigos) e modo "sem cidade".

**P2 · Comparação de bases ocupa altura excessiva.** `city_decision_ui._render_coverage` renderiza quatro métricas por alternativa, mesmo quando o usuário só precisa saber quantos destinos são mais rápidos, mais lentos ou não pesquisados. Preferir uma frase descritiva de leitura linear, preservando contagens, fonte, dados desconhecidos e tabela detalhada.

**P2 · README desatualizado.** O topo do `README.md` descreve uma aba antiga "Roteiro" com quatro subtelas. O código efetivo em `ux_navigation.py` oferece `Minha viagem`, `Explorar`, `Meu roteiro`, `Orçamento`. Atualizar o primeiro guia, sem apagar histórico.

**P2 · Acabamento mobile/a11y.** `assets/styles.css` já contém responsividade para cards, imagens e segmented controls, mas ainda cabe ajustar alvos de toque para 44px em telas estreitas e assegurar foco visível de controles nativos. Não substituir esses controles por HTML customizado.

## Revisão crítica B — abordagem UX (segunda passagem distinta, não ensaio humano independente)

- **Aceitar:** corrigir troca de cotação, acesso direto a preços pesquisados e seletor de destino; essas tarefas reduzem risco de erro ou interpretação técnica.
- **Aceitar com limite:** substituir os 4 indicadores por frase legível, **sem esconder** dados insuficientes, comparação entre bases, link das fontes ou tabela. Não declarar vencedor.
- **Aceitar com limite:** CSS responsivo e foco apenas em seletores já renderizados; não tocar no comportamento de layout de outras páginas com classes globais agressivas.
- **Rejeitar agora:** nova barra lateral, reescrita de navegação, novo dashboard e páginas para histórico/contabilidade. Não há evidência de ganho.
- **Pendência de aceite:** a auditoria B foi uma revisão crítica de critérios, **não** corresponde a um segundo agente isolado nem a um teste com duas pessoas. Para exigir independência real, é necessária revisão separada sobre o SHA do PR e inspeção visual humana.

## Métricas verificáveis e comparações

- **Cotação no Resumo:** antes: navegar para Detalhamento e clicar Carregar para ver no Resumo (duas ações + retorno). Alvo: uma ação de carregar **no próprio Resumo**. Contagem inferida pelo fluxo no código; validar em navegador.
- **Formulário de edição:** antes: namespace compartilhado entre IDs. Alvo: namespace único por `quote_id` + teste de alternância.
- **Comparação de bases:** antes: 4 widgets `st.metric` por candidata. Alvo: 1 bloco textual com as mesmas 4 contagens e 0 perda de dados.
- **Mobile 375/768/1280:** auditoria de screenshots, fluxo de teclado, scroll e tempos de conclusão permanece **não observada**; CI/AppTest não medem pixels ou leitor de tela.

## Limites de segurança e aceite

Preservar `TripPlan`, modelos de dinheiro, valores de orçamento, dados ferroviários e identidade GCS. Não salvar no GitHub público. Nenhuma UX pode tratar cotação histórica como reserva ou tarifa ausente como zero.

### Gate UX 3.10

Não há evidência concreta de necessidade de UX 3.10. Após inspeção real da 3.9, encerrar a sequência se os fluxos estiverem compreensíveis. Se aparecer bloqueio de acessibilidade ou tarefa, abrir issue pontual, não criar versão por obrigação.

**Integração:** somente PRs draft, sem merge/deploy sem aprovação. Documentação e revisões atualizadas depois de testes na branch da implementação.
