# UX94 — Visão financeira e simulações com complexidade progressiva

> Status: especificação para review; NÃO implementar código neste PR. O PR #207 (UX89) ainda está aberto: aguardar integração e estabilização, atualizar branch de implementação com main e revisar conflitos. Preservar UX64, UX81, UX83, UX85–88, REC02–REC05, TripPlan, wishlist UX502, arquivos privados e deep links antigos.

## Regras de execução
Atue como Principal Product Designer, Staff Python/Streamlit Engineer e Senior Code Reviewer. Audite o HEAD antes de mudar. Reutilize estado e componentes existentes; não crie segunda fonte de verdade, não invente preços/tempos/fotos/horários. Cada atividade tem cabeçalho único, uma CTA primária, secundárias contextuais e dados úteis antes de explicações técnicas. Não alterar widget keys já instanciadas no mesmo rerun. Atualizar AppTests, validar 1440/768/390 em navegador real (ou declarar limitação), executar suíte/contratos/CI no HEAD final. Nenhum merge com CI pendente/vermelho.

## Problema
Orçamento acumula seletores de modo oficial/simulação, ferramenta, cenário, estilo, duração, câmbio, aluguel, passeios e deltas, além de formulários de alternativa. A finalidade principal (custo/margem) perde destaque.

## Arquivos
`app.py`, `budget_sections_ui.py`, `unified_budget.py`, `rec04_simulation_ui.py`, `planning_context_ui.py`, `travel_advisor_ui.py`, `scenario_editor_model.py`, `quote_research_ui.py` e testes.

## Implementação solicitada
1. **Visão financeira** de leitura: teto oficial, projeção, margem, principais despesas, lacunas/fontes e CTA **Simular alternativa**. Não repetir o mesmo conjunto de números em múltiplos resumos.
2. **Simulações**: uma identidade de cenário **Hipotético — não altera meu planejamento**. Começar com a **pergunta concreta do usuário** (por exemplo, ‘quanto muda se eu ficar mais dias?’) e mostrar inicialmente somente 1–3 parâmetros relevantes à escolha. Teto, dias, cidade-base, aluguel e câmbio são capacidades existentes, **não cinco campos obrigatórios simultâneos**. Mostrar imediatamente total, margem, diferença versus oficial e custos desconhecidos; permitir expandir outros parâmetros quando necessários.
3. Estilos, saídas por semana, taxas/caução, bilhetes, ajustes por categoria e consultor só ficam em **Personalizar simulação** quando relevantes ao cenário; não mostrar `ux_mode`, `ux_budget_view`, `unified_scenario`, `unified_style` e `workflow_open_alternative` como entradas concorrentes.
4. Reusar cálculos, fontes e estados existentes, sem dupla contagem da verba de passeios, sem €0 para custos desconhecidos, e com moeda e referência temporal claras. Mudanças oficiais exigem pré-visualização e confirmação explícita, nunca efeito colateral de slider.
5. Preservar compatibilidade com links antigos, modo do consultor, citações de 2026 e datas set–nov/2027 não cotadas.

## Testes/aceite
R$60k/R$70k, 40–80 dias, bases alternativas, aluguel sem referência, FX, custos extras negativos, reserva, fonte live/snapshot; conferir equivalência dos cálculos atuais, nunca alteração silenciosa de TripPlan, UX64/REC04 e recuperação. AppTest e navegador 1440/768/390.

## Fora de escopo
Sem reescrever fórmulas/planilha oficial ou inventar cotações.
## Salvaguardas da revisão
- **Já existe:** visão financeira UX84, calculadoras/REC04, valores oficiais 60k/70k, simulação `unified_scenario` e fórmulas. Reutilizar sem novos modelos e sem nova entidade cenário.
- **Ajustar:** legibilidade, hierarquia, campos progressivos e comparação com oficial por intenção de uso. **Preservar:** fontes, moedas, reservas, variação/custos desconhecidos e confirmação explícita de mudança oficial.
- Não considerar custo desconhecido como zero, referência 2026 como cotação 2027 nem somar verba de passeios novamente.
- Testar que troca de campo/estilo/câmbio, troca de tela e retorno ao cenário deixam o TripPlan intacto até confirmação explícita.
