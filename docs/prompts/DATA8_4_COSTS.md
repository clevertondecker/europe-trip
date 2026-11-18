# DATA 8.4 — Orçamento de passeio para duas pessoas e premissas editáveis

**Papel:** Senior Finance + Product Engineer. **Dependência:** DATA 8.3.

## Objetivo
Calcular um orçamento **parcial e honesto**, sem converter desconhecido em zero e sem repetir tarifa de trem para atrações no mesmo destino.

## Implementar
1. Reutilizar as evidências do DATA 8.2. Entrada geral gratuita documentada deve ser diferente de visita guiada paga, de área externa sem bilhete e de preço desconhecido.
2. Registrar atividades opcionais com `source_url`, `checked_at`, unidade e validade, sem afirmar disponibilidade 2027. Piloto: visita guiada de adulto da Catedral de Aachen, € 8,50 no snapshot pesquisado.
3. Aceitar faixas **assumidas explicitamente pelo usuário** para transporte intermunicipal (uma vez por destino), transporte local e alimentação do casal, com min/max e método. Não buscar tarifa inventada.
4. Manter `partial_planning_range_eur` e lista de pendências; preencher `full_scenario_range_eur` somente quando todos os componentes tiverem números ou hipóteses de planejamento claramente fornecidas, e os ingressos necessários forem conhecidos.
5. Conversão EUR→BRL somente por taxa informada pelo usuário e marcada como hipótese, não câmbio ao vivo.
6. Não alterar orçamento oficial nem `unified_budget.py`, não misturar EUR e CHF e não afirmar compra, reserva ou valor definitivo.

**Aceite:** dois viajantes, tarifa ferroviária apenas uma vez por destino, atividade opcional separada, montantes desconhecidos nulos, duplo cômputo rejeitado, teste de €0 confirmado versus desconhecido e cálculos de faixas. A UI virá no DATA 8.5.
