# UX84 — Padronização visual de Orçamento | Prompt de implementação

## Papel e objetivo
Atue como Staff Streamlit Engineer, Finance UX Designer e Accessibility Reviewer. Modernizar as telas públicas Orçamento > Visão financeira e Orçamento > Simulações, seguindo EXATAMENTE o Design System compartilhado do UX81 e a identidade aprovada em Meu roteiro (PR #196), sem recriar cálculos financeiros nem misturar estimativas com valores confirmados.

## Dependência e pontos de entrada
Executar depois da implementação UX81. Ler o HEAD atualizado de app.py (ramificação page == "Orçamento"), budget_sections_ui.py (render_budget_summary), data_model.py, unified_budget.py, advisor_finance.py, predefined_budget_ui.py, research_cost_ui.py, quote_research_ui.py, ux44_finance_comparison_ui.py, rec04 e testes dos cenários antes de editar.
UX64 define as únicas duas tarefas públicas: "Visão financeira" e "Simulações". A tela de detalhamento continua acessível pelas rotas antigas, se aplicável.

## Visual e componentes compartilhados
- Cabeçalho, tipografia, cards KPI, botões, legendas, espaçamentos, cores de status e painéis de próxima ação devem ser os componentes UX81, não um sistema financeiro independente.
- Usar tons neutrals e cor de advertência somente para risco/ausência de evidência. Não usar cor para insinuar economia garantida.
- KPI com unidade/moeda, contexto de referência, fonte ou origem quando disponível; acomodar números longos sem overflow.
- Preferir próximo passo compacto e ferramentas visíveis em vez de um hero grande que esconda os dados.
- Uma única ação visualmente primária para cada estado, com ações exploratórias e documentação secundárias.

## Visão financeira
1. Evidenciar teto oficial, total de referência e margem de referência com cards coerentes com os indicadores de Meu roteiro.
2. Distinguir claramente orçamento planejado, estimativa histórica, cotação documentada, custo desconhecido e reserva confirmada; nunca rotular snapshot como dado live.
3. Dar visibilidade a despesas por categoria, avisos de ausência de cotações e data de referência. Não converter desconhecido em zero.
4. Manter acesso ao detalhamento/fontes, alertas de arredondamento e estados de indisponibilidade da sincronização.
5. O banner/next-action, se aplicável, deve orientar a simulação ou revisão de fontes, nunca sugerir compra/reserva já realizada.

## Simulações
1. Cabeçalho consistente e toolbar de cenário/estilo responsiva. Preservar seleção de teto 60k/70k, modo Oficial vs Simulação e controles de customização.
2. Gráficos/tabelas e resultado financeiro devem estar no centro, sem duplicar o cenário oficial em widgets independentes.
3. Diferenciar cenários experimentais de mudanças confirmadas: alterar uma simulação não modifica o plano salvo; só ações explícitas alteram valores oficiais.
4. Preservar cálculo original de moradia, alimentação, transporte, passeios, câmbio e integrações REC04; não reimplementar fórmulas na UI.
5. Mostrar gaps da fonte, cotação antiga e custos desconhecidos de forma neutra. Sem falso "economizado", desconto ou recomendação baseada em dados não comparáveis.

## Regras transversais
- CSS somente compartilhado/específico com escopo, nunca overrides que afetem Explorar/Planejar.
- Não mexer em TripPlan, data_model, unified_budget, schema, persistência, data provenance ou OAuth salvo se um defeito técnico exigir e for comprovado.
- WCAG AA >= 4,5:1, foco, teclado, controles e aviso de estado sem depender de cor; evitar gráficos como única representação de valores.
- 1440/768/390: cards quebram em coluna quando necessário, números monetários não truncam, inputs de cenário não espremem botões, tabelas scrolláveis internamente e não horizontalmente em toda a página.
- Zero-states para snapshot histórico, sem fonte, câmbio indisponível, custos desconhecidos e simulação incompleta.

## Testes necessários
- Cálculos e resumo invariantes antes/depois do redesign, com cenários 60k/70k.
- Simular estilo/customizar não escreve no plano oficial; confirmar explicitamente só no caminho canônico, se permitido.
- Alternar tabs não perde seleção nem corrompe sessão; custos ausentes preservam "desconhecido".
- Integridade REC04 / orçamento do roteiro e mensagens de fonte.
- Testes AppTest de Visão financeira, Simulações, detalhes antigos e navegação UX64.
- Testes de render HTML seguro, contraste, foco, responsividade em browser real (ou reportar não validado).

## Execução e aceite
Implementar código nesta branch após UX81; tests: python -m compileall -q . e python -m unittest discover -s tests -v; GitHub Actions no HEAD e screenshots desktop/mobile. Um PR de design NÃO pode aprovar números ou preços por aparência. Registrar limitações reais e não fazer merge automático. Inicialmente este PR contém somente o prompt e permanece draft até implementação.