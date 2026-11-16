# CSS 1.0 — Consolidação conservadora do Design System

## Objetivo
Reduzir as regras globais concorrentes criadas nas Fases 1/1B, sem redesenhar o Streamlit e sem alterar qualquer regra de negócio. Escopo: `assets/styles.css`, testes estruturais e esta documentação. A aplicação continua carregando **um único CSS** na mesma ordem pelo `app.py`; não foram criados múltiplos arquivos dependentes de importação, que poderiam mudar a cascata.

## Alterações
- Os dois blocos `:root` foram unificados; quatro tokens históricos `--petrol/--green/--sand/--muted` foram mantidos para compatibilidade.
- Os valores da paleta ativa foram centralizados nos novos `--ui-heading`, `--ui-selected`, `--ui-page-bg`, `--ui-link` e `--ui-focus`. Usar `var()` preserva os hexadecimais correspondentes.
- Foram removidas apenas declarações globais comprovadamente sobrepostas por seletores posteriores de mesma especificidade, com `!important`, ou por estilos mais recentes: fonte padrão antiga, fundo inicial do app/sidebar, cores antigas de h1–h3/links, medidas iniciais do container e cor inicial de métricas. A **font-size 2.65rem do h1**, não substituída pelo seletor posterior, foi preservada.
- Comentários históricos de fases foram substituídos por seções funcionais: base, home, componentes compartilhados, comparação, abas, navegação, atrações, dashboard, cenários, responsividade/acessibilidade.
- Mantidos todos os seletores específicos de tabs, segmented controls, foco visível e media queries; as regras `!important` remanescentes são em grande parte necessárias para prevalecer sobre estilos internos do Streamlit ou atender estados ativos.

## Cascata e decisões de não alteração
A fase moderna ainda especializa estilos de componentes já definidos na home original. **Não** fundimos automaticamente blocos de mesmos nomes se eles têm propriedades complementares, ou se estão dentro de media queries: deslocar uma declaração pode modificar o resultado final em certos breakpoints. Isso deixa alguns seletores repetidos **intencionalmente**, ao contrário de eliminar a repetição por força.

A configuração em `.streamlit/config.toml` mantém cores históricas para componentes nativos; CSS 1.0 não altera a configuração. Futuramente, uma única estratégia para personalização nativa deve ser investigada separadamente com aprovação de design.

## Testes
`python -m compileall -q .`
`python -m unittest discover -s tests -v`

`tests/test_css10_stylesheet.py` protege: um único `:root`, presença dos tokens, tipografia ativa, regras globais vencedoras, estados de tabs e segmented controls, acessibilidade/responsividade e smoke AppTest de navegação.

## Critérios visuais pendentes
**O CI não testa pixels reais.** Antes de aprovação final de layout, comparar Home, Explorar/Cidades-base/Comparar favoritas, Meu roteiro e Orçamento em 375, 768 e 1280 px, além de foco teclado, seleção de abas, botões e tabelas. Registrar qualquer alteração de contraste ou espaçamento com screenshot antes/depois e corrigir a regressão em novo commit. Esta entrega não afirma validação de screenshots no navegador.

## Integridade
Não alterar `TripPlan`, catálogo, GCS, Drive, API, finanças, autenticação ou deploy. Nenhuma nova dependência. PR isolado para revisão; sem merge automático.
