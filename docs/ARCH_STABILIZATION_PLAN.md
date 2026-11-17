# ARCH — Plano de estabilização pós-DQ3.2

O PR #91 foi integrado à `main` antes de iniciar esta frente. O PR #92 (correção de identidade e métricas das atrações, CI aprovado) também foi integrado antes desta branch.

## Visão de execução: cinco PRs menores, não um PR gigante

**ARCH 1.0 — Evidência histórica compartilhada (este PR).**
Reutilizar `rail_evidence_unified_model.route_evidence()` para os registros de operadores e uma única função de fallback para as referências `exploration_bases_2027`. Migração inicial de `outing_base_coverage_model.py`, `dq31_logistics_evaluation_model.py` e `dq32_macro_opportunities_model.py`. Preservar fonte, mínimo/típico, valores `None`, compatibilidade das saídas, e testes de equivalência entre as três telas. **Não** alterar dados ou cálculos de tarifas.

**ARCH 1.1 — Estado canônico do TripPlan.**
Auditar consumidores reais de `advisor_plan`, `explore_packages`, `explore_calendar`, `explore_base`, `unified_city`, `unified_scenario`. Manter `planning_session` como fronteira de mutação. Substituir os leitores duplicados por seletores derivados antes de remover qualquer chave. Testar backup e `create_from_legacy()`, incluindo arquivos históricos. Nenhuma remoção sem evidência de que não há consumidores.

**ARCH 1.2 — Decomposição incremental do `app.py`.**
Inventariar responsabilidades e dependências; extrair primeiro funções puras (apresentação e transformação de dados) e, depois, componentes e configuração. Preservar `app.py` como entrypoint de Streamlit, imports públicos, callbacks, sincronização Drive, autenticação, cenários, CSS e fluxo de navegação. Comparar AppTests antes/depois. Não realizar reescrita em lote.

**ARCH 1.3 — Reprodutibilidade de CI e contratos de datasets.**
Introduzir lint aplicado a código novo/modificado, testes de schema/proveniência e checagem de imports; adicionar lockfile ou constraints compatíveis com Python 3.11 e implantação Streamlit, após auditoria de dependências. Separar testes rápidos e AppTests sem perder cobertura. Nenhuma formatação massiva nem atualização indiscriminada de bibliotecas.

**ARCH 1.4 — Performance medida e limpeza segura.**
Instrumentar tempo de carregamento/rerun do Streamlit, obter linha de base e otimizar somente gargalos comprovados. Cache para operações puras versionadas e índices por ID quando validados. Antes de remover código histórico, auditar imports dinâmicos, backcompat e arquivos restauráveis. Documentos de pesquisa históricos ficam preservados.

### Contrato de entrega comum
Cada PR parte da `main` mais recente, modifica apenas seu domínio, passa por `compileall`, toda a suíte `unittest` e AppTests pertinentes, apresenta diferença antes/depois e não altera o TripPlan, o plano oficial, fontes históricas ou o deploy sem autorização.

## ARCH 1.0 — Diagnóstico concreto e contrato

Antes, as três consultas abaixo repetiam a sequência: seleção em `rail_evidence_unified_model.route_evidence()` → fallback do estudo `exploration_bases_2027` → montagem manual de `minimum_oneway_min`, fonte, dataset e data:

- `outing_base_coverage_model.preview_for_base()`
- `dq31_logistics_evaluation_model.logistics_comparison()`
- `dq32_macro_opportunities_model.opportunity_overview()`

Agora as três consomem `evidence_query_model.get_rail_evidence(base_id,destination_id,rail=None,exploration=None)`. O retorno mantém status, fonte, data, dataset, duração mínima histórica, duração típica quando publicada pela mesma evidência, lista defensiva de observações alternativas e justificativa de seleção.

**Precedência de exibição:** (1) o adaptador unificado seleciona, na sua ordem já documentada, `five_base_operator_2026`, `expanded_rail_sample_2026`, `four_base_routes_2026`, `dq30_dated_operator_2026`, `dq30_operator_overview_2026`; (2) caso nenhum registro contenha tempo de ida, fallback para `exploration_bases_2027` com duração válida e URL HTTPS; (3) se nenhum tempo válido existir, `None` e status de pesquisa parcial/ausente. Origem e destino idênticos recebem `local`, com duração de acesso local desconhecida, não zero.

**Refinamentos da revisão ARCH 1.0:** quando o fallback exploratório é selecionado, sua observação é adicionada a `observations` junto das observações parciais já existentes, com `selection_role=selected_fallback`, duração mínima, data, dataset e URL da fonte. A duração exploratória aceita exclusivamente `int` positivo, conforme o contrato de `load_exploration()`; números `float`, `bool`, strings e durações não positivas não são aceitos. Testes cobrem fallback sobre observações unificadas parciais sem tempo e imutabilidade das fontes.

**O que a seleção NÃO faz:** menor tempo de ida ≠ tempo típico, retorno, custo normal, viagem porta a porta ou acesso comprovado. A precedência não significa que fontes menos prioritárias sejam descartadas. Não converte Haversine nem presume retorno.

**Limite deste primeiro recorte:** `base_coverage_model._dataset_routes()` ainda possui política própria de evidências **documentais** para a cesta fixa de 15 destinos e contagens históricas. Não foi migrada automaticamente porque a cobertura documental possui flags de frequência/conexão e testes legados distintos; auditar equivalência e migrá-la em um follow-up ARCH 1.0b caso os resultados difiram. Os adaptadores de caminhada e moradia permanecem especializados, não foram recriados artificialmente.

## Critérios de aceite ARCH 1.0

1. A seleção de Lille → Bruxelas produz o mesmo tempo, fonte e estado nas três visões consumidoras.
2. Unificação preserva durações típicas somente quando pertencem à evidência selecionada.
3. Fallback histórico é usado **apenas** quando o adaptador unificado não tiver duração válida.
4. Uma rota local permanece desconhecida, sem custo ou duração presumida.
5. Campos e datas desconhecidos permanecem `None`; `return_2027_verified=False`.
6. Números de origem, destinos e cobertura da cesta DQ3.1 permanecem compatíveis.
7. Nenhum arquivo JSON, TripPlan, CSS, mapa, estado de sessão ou autenticação é alterado.
8. AppTests já existentes continuam passando; sem merge/deploy automático.

## Próxima decisão

Após revisão e CI, avaliar se `base_coverage_model._dataset_routes()` pode aderir à consulta comum sem modificar o significado de completude documental. Apenas então avançar com ARCH 1.1.
