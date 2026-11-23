# UX101 — Ficha individual de cidade-base: contexto, síntese e ações

> **STATUS: ESPECIFICAÇÃO PARA REVIEW — NÃO IMPLEMENTADO.** Este PR contém apenas este prompt. Não alterar código de produção, criar screenshots fictícias ou fazer merge como se a tela estivesse pronta.

## Contexto verificável

Repositório: `clevertondecker/europe-trip`.
Fluxo real: `Explorar → Comparar bases → Cidade para investigar individualmente → Conhecer cidade`.
Origem: `rec03b_handoff_ui.render_card_selection_summary()` → `render_card_actions()` → `queue_handoff(...,"profile",[base])`; destino: `render_profile_context(plan)`, que chama `base_research_expanded_ui.render_expanded_research(activity_override="Explorar uma cidade", compact=True, fixed_city=base)`.

Na tela atual aparecem, em sequência: título genérico “Explorar cidades-base”, botão de retorno, legenda da cidade, três ações empilhadas, outro título “Explorar cidades”, “Explore uma cidade”, nome da cidade, duas métricas soltas e longa pilha de relatórios em accordions. A interação é funcional, mas não responde rapidamente ao usuário *por que vale investigar essa cidade*, *que informações são verificadas* e *qual ação pode realizar*.

A tela de referência enviada mostra **Mulhouse · França**, “Alsácia–Basel · Finalista”, **3 anúncios históricos de 2026** e **7/15 tempos na cesta histórica comparável**. Esses valores são exemplos de dados já exibidos naquela sessão, **não fixtures hardcoded nem notas de qualidade**.

## Objetivo

Criar uma **ficha de investigação individual**, clara e consistente com o design system UX81/UX96/UX99/UX100, que mantenha o contexto da comparação selecionada e organize:

1. Identidade da cidade e classificação **de pesquisa**, sem sugerir aprovação do roteiro;
2. Ações nativas agrupadas por prioridade;
3. Resumo rápido em cartões compreensíveis;
4. Painéis “O que está documentado” e “O que falta confirmar”;
5. Continuação natural aos detalhes (responsabilidade UX102).

Nenhum wizard, formulário de confirmação extra, segundo estado de seleção ou nova persistência.

## Inspecionar antes de codificar

- `rec03b_handoff_ui.py`: `render_profile_context`, `render_card_actions`, `_favorite`, `return_to_suggestions`, `context_for`;
- `rec03b_handoffs.py`: `CONTEXT`, `CHOICE`, `queue_handoff`, validações do contexto;
- `base_research_expanded_ui.py`: `render_expanded_research`, `_explore_city`, `_city_profile`;
- `base_research_expanded_model.py`: `load_research(include_candidates=True)`, `find_city`, `observed_housing`, `decision_readiness`;
- `base_coverage_model.py`: `coverage_matrix("general", study=study)`;
- `city_profiles_model.py` / `city_research_packs_model.py`: descrições, vida cotidiana, fontes;
- `rec04_candidate_capabilities.py` e `rec04_simulation_handoff.py`: quando simular é permitido;
- `ux41_favorites_model.py`: favoritos e seu limite;
- `ux100_base_card_photos.py` e serviço existente de imagens, se reuso for compatível;
- `ux_shared_ui_presentation.py`, `assets/styles.css`, testes de handoff.

Confirmar HEAD da `main` e não refazer o que já existe.

## Layout-alvo (ordem visual)

### A. Navegação e cabeçalho contextual

No topo:
- Breadcrumb editorial curto: `Comparar bases / Investigar cidade` (não precisa ser link se a ação nativa Voltar estiver ao lado);
- Botão nativo **Voltar à comparação**, preservando `CHOICE`, escopo e filtros;
- Título principal único: **Mulhouse, França** (dinâmico);
- Linha contextual com corredor `Alsácia–Basel` e status factual `Finalista da pesquisa` / `Candidata`;
- Distinção explícita, quando pertinente, entre `base oficial atual`, `elegível para oficialização` e `somente exploração`. `shortlist=True` **não** equivale a base oficial ou recomendada.
- Subtítulo orientador: “Conheça as evidências disponíveis antes de decidir se vale aprofundar esta cidade.”

Eliminar os títulos repetidos **“Explorar cidades” / “Explore uma cidade”** apenas no caminho `fixed_city` do perfil; preservar os títulos adequados dos demais pontos de entrada em `render_expanded_research`.

### B. Ações agrupadas e realmente funcionais

Uma faixa horizontal em desktop, empilhamento no mobile:

- **Simular esta cidade**: ação principal **somente quando a capacidade real permitir**. Reutilizar `request_simulation` e validar a disponibilidade em `rec04_candidate_capabilities`. Caso indisponível, explicar o motivo e não fingir uma simulação.
- **Ver cidade e destinos no mapa**: reutilizar `queue_handoff(...,"map",[base])`.
- **Adicionar/Remover favorita**: reutilizar `_favorite`, `MAX_FAVORITES`, estado existente e aviso real de persistência; não rotular como “salva” antes de confirmação.
- **Voltar à comparação**: `return_to_suggestions`, sem perder escopo nem seleção.

Sem `<button>`, `onclick`, navegação falsa em HTML; `st.button` e callbacks nativos apenas. Agrupar visualmente, não aumentar o número de decisões.

### C. “Cidade em resumo” — cartões factuais

Exibir até **três métricas**, condicionais à disponibilidade:

- **Moradia pesquisada**: `observed_housing(city)["count"]`, rótulo “anúncios históricos · 2026”, sem chamar de aluguel disponível;
- **Tempos pesquisados**: `coverage_matrix("general", study=study)` → `route_basket_with_time / route_basket_total`, rótulo “cesta histórica comparável”, não “X destinos bons”;
- **Mobilidade ou contexto urbano**: resumo derivado de evidência municipal existente (`city_profiles_model` / research pack), quando concreto e com fonte. Exibir estado “Pesquisa pendente” se nenhum fato correspondente estiver documentado. Nunca hardcode “Bonde” para cidades sem essa referência.

Não confundir fontes históricas de 15 destinos com o escopo atual confirmado em REC03A. Identificar as duas coberturas quando coexistirem. Não transformar cobertura em score ou ranking. Manter tooltip/legenda acessível para “7 de 15”.

### D. Dois painéis de síntese

À esquerda, `O que está documentado` (semântica positiva/verde leve, mas *não* “melhor base”):
- até 3 fatos curtos **com proveniência ou código de evidência real**: corredor identificado, mobilidade pesquisada, anúncios históricos, fontes municipais, etc.
- usar somente `city_profiles_model`, `decision_readiness`, dados de pesquisa e outras projeções existentes.

À direita, `O que falta confirmar` (âmbar, sempre factual):
- cobertura ausente ou parcial da cesta aplicável;
- custo/disponibilidade/contrato para 2027 não cotados;
- retorno, frequência e última milha não verificados;
- incompatibilidade com modelo oficial, quando aplicável.

Não deduzir “aluguel barato”, “boa conectividade”, “segurança”, “ideal para home office”, “qualidade de vida” ou “vencedora” só por existirem fontes. Se nenhum ponto positivo for comprovado, mostrar **estado neutro** em vez de cartão verde vazio. O máximo de bullets é uma diretriz visual, não apagar informações importantes: demais dados permanecem nos detalhes UX102.

### E. Fotografias (apenas se seguras)

Fotografia no hero é **opcional**. Reaproveitar assets/licenças já verificadas no serviço de fotos UX100 ou catálogo existente **se e somente se** o ID corresponder à cidade, houver autoria, licença e fallback confiável. Não reutilizar imagem genérica ou de outra cidade, nem gerar uma imagem artificial para implementar a tela. Sem foto verificada, hero com identidade tipográfica e fundo sutil.

## Design e implementação

- Preferir `st.container(key=...)`, `st.columns`, `st.metric` e apresentação HTML **estática/escapada** somente onde agregar valor;
- Reutilizar CSS10/UX81 e classes namespaced `ux101-*` sem atingir outras páginas;
- Não criar um segundo perfil ou duplicar `_explore_city`: decompor a apresentação para receber `fixed_city` / flag `show_overview` quando adequado;
- Evitar CSS baseado em hashes internos do Streamlit, manipulação de DOM, JS e scroll artificial;
- A ação principal não pode sofrer erro se `capability_for` sinalizar indisponibilidade;
- Nenhum write em `TripPlan`, `scenario_base_selected` ou no escopo ao apenas renderizar.

## Testes e regressões (obrigatórios antes de merge)

- AppTest real: selecionar cidades em Comparar bases → escolher “Cidade para investigar individualmente” → “Conhecer cidade” → tela contextual com título correto;
- Cidade `Mulhouse` (suportada) e cidade apenas exploratória (não oficializável);
- Com 0/1/2+ favoritos, adicionar/remover, testar limite e preservar o indicador de dirty sem alegar salvamento;
- Simular elegível/inelegível, ida ao mapa e retorno à comparação; preservar `CONTEXT`, `CHOICE`, wishlist, escopo REC03A e `advisor_plan`;
- Sem informações de moradia, sem tempos, sem pesquisa urbana; nenhum texto favorável inventado;
- Títulos não duplicados no `fixed_city`, mas exploração independente continua funcionando;
- Componentes HTML escapam nomes e textos não confiáveis;
- Acesso por teclado e foco.
- Executar `python -m compileall -q .`, `python tools/validate_research_data.py`, `python -m unittest discover -s tests -v`.

## Aceite de produto

Ao acessar a ficha individual, sem rolar longamente, o usuário identifica: cidade, corredor, status **de pesquisa**, o que se sabe, o que falta confirmar e a próxima ação viável. Ao voltar, encontra exatamente a comparação e os destinos que havia selecionado. A página não finge que `3 anúncios` representam disponibilidade em 2027 nem que `7/15` é uma nota de cidade.

**Entrega deste PR atual:** somente esta especificação para review. **Implementação futura:** PR funcional próprio, após aprovação; não fazer merge automático.
