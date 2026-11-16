# UX 4.4 — Comparação financeira exploratória e parcial

## Diagnóstico
O aplicativo possui `unified_budget.py`, `advisor_finance.py` e modelos de simulação da cidade-base; estes não devem receber custos de excursões ou aluguel já provisionados como acréscimos automáticos. Referências de 2026 não são cotações para 2027.

## Implementação
- `ux44_finance_comparison_model.py` é um modelo puro de cenários para duas ou três cidades, 60 noites, dois adultos, com categorias: moradia, taxas, contas e internet, supermercado, restaurantes, transporte urbano, passeios.
- Valores explícitos devem ser informados para **o período inteiro e para o casal**; valor em branco permanece desconhecido. Zero informado conscientemente não equivale a campo vazio.
- O resultado é **subtotal hipotético**, nunca custo total completo. Caução é caixa comprometido e não gasto. Comparações entre cidades consideram somente categorias com entrada em todas elas.
- `ux44_finance_comparison_ui.py` integra um expansor no comparador de favoritas, apresentando referências de aluguel já existentes e inputs opcionais, sem criar outra página.
- Informações não são aplicadas nem duplicadas no orçamento oficial; não alteram `TripPlan`, favoritos, backup ou Google Drive.
- Campos históricos com referência documental exigem fonte. A UI permite hipóteses manuais; não promove amostras heterogêneas a valores financeiros automáticos.

## Limitações
Cotações reais de 2027, condições da locação, disponibilidade, taxas, internet e retorno ferroviário continuam desconhecidos. Subtotal não é economia garantida. Validação visual em desktop e mobile ainda é necessária, independentemente de AppTest.

## Testes
`python -m compileall -q .`
`python -m unittest discover -s tests -v`

## Coordenação
PR independente da UX 4.3. Quando integrado, a interface financeira usará a matriz ferroviária atualizada sem recalcular gastos automaticamente.
