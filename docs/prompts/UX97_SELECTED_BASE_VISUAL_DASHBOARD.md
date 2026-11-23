# UX97 — Comparador visual da seleção (matriz + resumo)

Repositório: `clevertondecker/europe-trip`. PR **empilhado sobre UX96**, que fornece CSS e cartões reais. **Não fazer merge isoladamente sem UX96**.

## Problema a resolver
Na tela atual, a decisão aparece como quatro linhas de texto com contagens, enquanto a matriz de deslocamentos está atrás de checkbox. O usuário precisa de uma **matriz visual principal e clara**, com comparação das 2–5 bases que ELE selecionou em CHOICE e os mesmos destinos confirmados no escopo. A prévia UX95 das cidades sugeridas é secundária e deve ficar recolhida quando a comparação escolhida existe.

## Entrega obrigatória
- Em `ux87_inline_base_comparison_ui.py` usar a projeção existente `project_inline_comparison()` (sem modificar regras). Mostrar tabela por destino **aberta por padrão**, nome das bases nas colunas e destino nas linhas, células com `display_min` e status **histórico / indicativo / local / não pesquisado**.
- Usar HTML sem JS, escapado com `html.escape`, CSS local `ux97-*` fornecido por UX96, `role="region"`, foco por teclado, tabela semântica `table/th scope/td`, rolamento horizontal no celular e cabeçalho de destino fixo quando suportado. Não replicar tabela como formulário interativo.
- Painel de resumo factual ao lado (3:1 em desktop, empilhamento no mobile): `common_timed_destination_ids` e contadores canônicos, **não** ranking de melhor base, notas de custo/qualidade, conectividade presumida ou economia inventada. Apresentar lacunas: retorno, frequência, última milha e horários de 2027.
- Colocar detalhes narrativos de cada base, imperdíveis, pesquisas pendentes e caveats no expander nativo existente. O controle legado `rec03a_inline_matrix` continua com mesma chave e tabela técnica opcional; `rec03a_inline_sources` continua fonte original. Não quebrar AppTests antigos, nem tornar fontes inacessíveis.
- O badge `Histórico` **não** significa horário/custo de 2027 confirmado. Tempo é **mínimo de ida**, nunca porta a porta ou ida e volta. Se `display_min is None`, **nenhum número** em célula, mesmo se categoria local.
- Não mostrar fotos nesta etapa. O esboço aprovado é **sem fotos**; HTML estático jamais deve fingir que é botão.

## Contratos que não podem mudar
`CHOICE` e `render_card_choice()` permanecem fonte única de seleção (2–5); filtros, wishlist, `TripPlan`, `REC03A/B`, UX85–UX95 e `routes7_comparison_projection.decorate_comparison()` intactos; dados brutos de fontes e ressalvas expostos sob demanda.
A representação visual é apenas projeção dos registros existentes; sem inventar dados, ranking ou nova persistência.

## Testes e revisão
- Teste 2/3/5 bases, mesmo destino por coluna, categorias local/sem tempo, tempo desconhecido, fontes divergentes, ressalvas ferroviárias, dados vazios e nomes HTML escapados.
- AppTest real do fluxo: confirmar escopo → selecionar 2 bases → tabela aparece **sem acionar outro checkbox** → expandir fonte/tecnical → alternar seleção → voltar a Explorar sem alterar TripPlan/wishlist.
- CI: `python -m compileall -q .`, `python tools/validate_research_data.py`, `python -m unittest discover -s tests -v`. Fazer screenshot em 1440/768/390px **em navegador real** antes do merge; nenhum screenshot gerado por imagem é prova de implementação.
- Exigir aprovação do UX96 antes do UX97; manter este PR em draft até passar.
