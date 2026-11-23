# PROMPT DE IMPLEMENTAÇÃO — UX96: comparador visual com hierarquia real

Atue como Staff Python/Streamlit Engineer, Principal Product Designer e Accessibility Engineer no repositório `clevertondecker/europe-trip`. **Este PR inicial contém somente especificação; implemente o código nesta mesma branch após revisão.** Não fazer merge de documentação como se a tela estivesse pronta.

## Evidência e objetivo
A tela atual (após UX95 #214) mostra "Comparando Mulhouse, Colmar" seguido por parágrafos de contagens e uma matriz atrás de checkbox. O esboço enviado anteriormente com fotos e tempos era ilustrativo, **não** prova que esses assets, preços ou tempos existam. O alvo realista é um painel Streamlit/CSS usando somente dados canônicos.

## Arquivos para inspecionar
`ux87_inline_base_comparison_ui.py`, `rec03a_suggestions_ui.py`, `rec03b_handoff_ui.py`, `rec03b_handoffs.py`, `ux_shared_ui_presentation.py`, `assets/styles.css`, `docs/CSS10_DESIGN_SYSTEM_AUDIT.md` e testes `test_ux87_inline_base_comparison.py`, `test_ux95_visual_base_comparison.py`.

## Implementação
1. Em Explorar → Comparar bases, apresentar "Sua comparação" **antes** dos blocos longos de pesquisa, assim que CHOICE tiver 2–5 bases. O topo apresenta chips/indicadores de cidades escolhidas e número de destinos do escopo confirmado; seleção continua exclusivamente no fluxo CHOICE existente. Não criar multiselect, form, estado espelho ou botão de confirmação.
2. Para 2–5 bases, criar cartões compactos, responsivos, com nome e país, 4 contagens reais (historical, reference_only, local, no_time), indicação de seleção e resumo da cobertura. Não mostrar nota "excelente", custo de hospedagem, preço, vencedor ou "melhor" sem dados verificados.
3. Foto **somente se já houver imagem real com licença/proveniência resolvida** no catálogo. Caso contrário usar placeholder neutro **sem imagem inventada**, sem URL de stock. As fotos não são obrigatórias para atingir qualidade visual.
4. Resumo lateral com `st.columns` em telas largas: número de destinos com referências em comum, cobertura por base e principais lacunas dos imperdíveis. Não apresentar ranking; a síntese é factual. Em mobile, resumo empilha abaixo da matriz.
5. Remover os quatro parágrafos repetitivos de `st.write` do corpo principal de `render_inline_comparison`, mantendo as informações em componentes escaneáveis e expanders. "O que falta verificar" sempre legível.
6. Usar classes **namespaced** `et-base-compare-*` em `assets/styles.css`, tokens CSS10 existentes, HTML somente para elementos estáticos; controles interativos devem ser Streamlit nativos. Sem CSS global para `stCheckbox`, `stDataFrame` ou outros módulos.
7. Deixar evidente "Prévia das sugestões" versus "Sua comparação", sem duas matrizes abertas competindo. Preservar busca/paginação das 34 candidatas e limite de 5 seleções.

## Critérios de aceite
- 0 bases: descoberta; 1: informações individuais; 2–5: cartões + resumo + matriz na mesma página e sem segundo clique.
- Dados reais somente: não inventar tempos, preços, classificação ferroviária, imagens, scores, rankings ou atrativos.
- `TripPlan`, wishlist, `CHOICE`, escopo confirmado e projeções REC03A/UX503/ROUTES7 permanecem imutáveis por renderização.
- AppTests para 0/1/2/5 bases, alteração de seleção, cenário sem evidência e ordem dos componentes.
- Screenshots reais de execução Streamlit em 1440/768/390 px, com evidência de overflow e sem placeholder falso. CI verde e review adversarial antes do merge.

## Dependência
Implementar UX96 antes de UX97 e UX98. A especificação não equivale a código entregue.
