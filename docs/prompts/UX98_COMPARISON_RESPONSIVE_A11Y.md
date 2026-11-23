# PROMPT DE IMPLEMENTAÇÃO — UX98: responsividade, design system e validação visual

Atue como Principal UX Engineer, Streamlit Engineer e Accessibility Reviewer. **PR inicialmente documental**; após UX96 e UX97, atualizar a branch com a `main` e implementar os ajustes reais.

## Objetivo
Evitar que a comparação final volte a parecer HTML sem CSS ou que quebre em telas menores. O alvo é a implementação Streamlit real, não uma imagem estática.

## Implementação
1. Auditar todos os novos componentes de UX96/UX97 e CSS10 em `assets/styles.css`; garantir classes `et-base-compare-*`, tokens existentes, sem estilos globais acidentais ou `unsafe_allow_html` aplicado a dados não escapados.
2. 1440px: cards de cidade em grid, matriz dominante e resumo ao lado, sem textos longos. 768px: cards em 2 colunas ou coluna única, resumo abaixo, matriz com rolagem local. 390px: coluna única, sem scroll horizontal da página; scroll horizontal apenas da tabela, indicação de que há mais cidades, toque confortável e rótulos completos.
3. Estado de foco de teclado, contraste WCAG AA, leitura por screen reader, não depender só de cor para categoria. Preservar link real para fonte e data. Garantir que placeholders de imagem sejam neutros e não sugiram fotografia disponível.
4. Renderização sem JS injetado, sem `st.components` para interação duplicada, sem CSS que dependa de hashes de classes geradas pelo Streamlit. Degradar com segurança quando a imagem real falhar.
5. Não alterar `CHOICE`, `TripPlan`, wishlist, escopo confirmado, evidências, ranking ou cálculos. Testar 0/1/2/3/5 bases, filtros, 34 candidatas, destinos sem tempo, prioridade e seleção/deseleção.
6. Registrar screenshots **do aplicativo executado**, não de imagem gerada; desktop 1440, tablet 768 e mobile 390. Registrar diferenças com o protótipo e justificar as inevitáveis por limitação Streamlit. Evitar prometer equivalência pixel-perfect com imagem conceitual.
7. Testes de regressão AppTest e CI; revisão adversarial de CSS, acessibilidade, semântica e componentes reutilizáveis. Sem merge enquanto houver overflow, controles falsos ou regressões.

## Critérios de aceite
A comparação tem hierarquia legível, matriz aberta, resumo contextual e fontes acessíveis em todos os tamanhos. Não há fotos, valores ou ratings inventados.

## Dependência
UX96 → UX97 → UX98. A criação deste prompt não significa que a implementação visual já ocorreu.
