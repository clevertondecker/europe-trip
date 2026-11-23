# PROMPT DE IMPLEMENTAÇÃO — UX97: matriz visual de tempos como foco principal

Atue como Staff Streamlit Engineer, Data Quality Reviewer e Product Designer. **PR inicialmente documental**. Implementar depois de UX96 integrado, atualizando a branch para o HEAD de `main`.

## Problema
Em `ux87_inline_base_comparison_ui.py` a matriz da comparação escolhida está atrás de `st.checkbox("Ver matriz de trajetos por destino")`; ao abrir usa `st.dataframe` cru com `label` longo. UX95 também criou uma matriz de prévia para cidades sugeridas. A tela atual é texto técnico, não uma visão lado a lado.

## Implementação
1. Em `render_inline_comparison`, mostrar a matriz principal **aberta por padrão** quando 2–5 cidades estiverem em `CHOICE`; sem checkbox-gate. A prévia UX95 deve permanecer identificada e recolhida quando a comparação real estiver ativa.
2. Linhas = destinos do escopo confirmado, na ordem canônica, destacando `must_visit`; colunas = 2–5 bases selecionadas, na ordem de `CHOICE`. Nada de mistura de escopos, nem "melhor" por comparação de subconjuntos diferentes.
3. Projetar cada célula de `projection["cells"][(base,id)]` como `display_min` formatado, categoria `historical/reference_only/local/no_time`, e sinal de ressalvas. Nunca reconstruir ou alterar `project_inline_comparison`, `decorate_comparison` ou fontes ROUTES7.
4. Cores semânticas discretas **sempre acompanhadas por texto**: Histórico (verde), Indicativo (azul), Acesso local pendente (âmbar), Sem tempo pesquisado (cinza). Divergência de fontes/estação e observações relevantes ganham `ver ressalvas` na célula e explicação acessível.
5. Priorizar componentes reais e testáveis de Streamlit (`st.dataframe` com `column_config`/pandas Styler quando seguro, ou tabela HTML **estática** escapada; nunca controles HTML inertes que imitam botões). Caso a solução nativa não permita badge + acessibilidade, usar tabela HTML sem eventos JS e ações nativas externas para detalhes.
6. Cabeçalho legível, zebra discreta, primeira coluna claramente distinguível, rolagem horizontal em 5 bases, nenhum truncamento silencioso; legenda visível e fonte/metodologia sob `st.expander` sem esconder a matriz.
7. Painel lateral UX96 deve resumir apenas cobertura documental e lacunas reais; não criar "custo médio", "melhor conectividade", "usar cidade vencedora" ou tempos hipotéticos. Separar referência histórica de horários de 2027.

## Testes
- Testes puros de projeção: 2/3/5 bases, prioridades, categorias, ausência de tempo, tempos válidos, ressalvas, mesma ordem/escopo e imutabilidade.
- AppTests: matriz visível sem clicar; nenhuma duplicação de matriz ativa; seleção dinâmica e estado de dados incompletos; links de fontes e ressalvas; sem segunda seleção.
- Review visual desktop/tablet/mobile e pipeline completa. Nenhum merge antes de CI verde e aprovação de UX.

## Dependência
UX96 primeiro. Este PR de prompt não implementa a matriz até haver commits de código.
