# UX96 — Shell visual da comparação de cidades-base

Repositório: `clevertondecker/europe-trip`. Base: `main`. Escopo **apresentação e layout**.

## Contexto e objetivo
A tela real após UX95 exibe muitos blocos de texto e checkboxes; o esboço visual anterior incluía fotos e tempos não verificados. Implementar um **dashboard Streamlit viável**, próximo do tema existente (`assets/styles.css`), **sem criar fotos, valores turísticos, custo, score, badges de “vencedor” ou rota 2027**. Nesta branch, os cartões são intencionalmente **sem foto** (ícone e nome reais). Os dados vêm integralmente de `recommend_bases()`.

## Entregas desta etapa
1. Faixa de contexto com **as bases selecionadas em CHOICE** e contagem do escopo REC03A. A faixa é somente projeção, não novo multiselect.
2. Cartões de cidade em grade responsiva com nome real, país, estado selecionado, referência à base oficial e quatro classes da evidência: histórico, indicativo, local pendente e sem tempo.
3. Preservar checkbox nativo `render_card_choice()` com chave `rec03a_pick_<id>`, até cinco cidades, navegação, busca/paginação e detalhes/fonte `rec03a_details_<id>`. Não disfarçar um componente HTML estático como botão.
4. CSS com classes `ux96-*` e `ux97-*` **escopadas**; sem alterar regras globais ou adicionar dependências de JS/React.
5. Não inventar fotografia; se futuramente houver imagem real licenciada, ela só poderá ser mostrada com fonte, crédito, fallback e cobertura verificados, em PR separado.

## Critérios observáveis
- Desktop 1440px: faixa de seleção e cartões em duas colunas legíveis, sem cartões verticais gigantes; 768px sem overflow descontrolado; 390px com controles utilizáveis e sem texto cortado.
- Sem 2ª seleção: um único CHOICE e mesmos callbacks. Mudança de prioridade na wishlist ou de escopo não reaproveita contagem obsoleta.
- Base oficial não significa escolhida; histórico não significa confirmado em 2027; referência indicativa visualmente distinguível; zero desconhecido não vira zero minutos.
- Rerun ao marcar/desmarcar e alternar busca/filtros/página mantém escolhas e não altera `TripPlan`, `ux502_interests` ou projeções ferroviárias.
- HTML gerado com `html.escape` para textos do catálogo; CSS reutiliza tokens atuais e mantém contraste/foco/teclado.
- Novo `tests/test_ux96_comparison_visual_shell.py` e regressões UX85/UX95. Exigir `compileall`, `validate_research_data.py` e suíte de unittest.
- Validar visualmente em navegador **real**: AppTest e CI não são screenshots.

## Dependência
UX97 (PR seguinte, criado sobre esta branch) tratará **a comparação das cidades selecionadas UX87** como matriz principal sempre aberta, resumo de evidências e fontes progressivas. Não implementar outra comparação nem ranking aqui.

## Estado
Implementação inicial incluída nesta branch; manter PR em draft até pipeline e review visual. Não fazer merge sem autorização.
