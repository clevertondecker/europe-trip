# Pesquisa de moradia para decisão de cidade-base — 56–60 noites

Implementação adicional aprovada na revisão estratégica (não substitui o snapshot #108). Contrato estrito para avaliar **duas pessoas** em cidade-base cadastrada, a partir de **05/09/2027**, por **56–60 noites**.

O dataset atual contém 30 bases, 35 observações históricas e **zero cotações elegíveis para 2027**. Os preços mensais não são convertidos automaticamente em reserva de dois meses. O código não consulta anúncios em tempo real, não oferece unidades para reservar nem indica uma cidade vencedora.

## Checklist vinculante
- Datas idênticas de entrada/saída, 2 adultos, imóvel privativo e mobiliado e permissão para temporada.
- Disponibilidade verificável em página de anúncio direto; confirmação de cozinha, lavanderia, internet, espaço para trabalho e acesso real ao transporte público.
- Total da estadia com aluguel, limpeza, taxas obrigatórias, serviços e utilidades, na moeda da fonte.
- **Depósito reembolsável** separado da despesa: impacto no caixa mostrado sem contá-lo como gasto definitivo.
- Dado ausente é `None`, não zero. Fonte HTTPS + data; valores validados estruturalmente ainda exigem nova conferência de disponibilidade.

**P1:** escolher base por aluguel mensal histórico; sem 3 opções comparáveis para as datas, decisão pendente. **P1:** dupla contagem do depósito e omissão de taxas; contrato separa `expense_total` e `upfront_cash_exposure`. **P2:** comparações com datas/idiomas/moedas diferentes; exibir incomparabilidade, sem auto-score.

**Contratos reutilizados:** `load_research()`, `observed_housing()` e premissas de seleção do comparador. **Aceite:** zero falso 2027 confirmado, testes de dia/casal, totais, depósito, campos pendentes e comparação da mesma janela; sem alteração da cidade-base oficial, wishlist, TripPlan, UI ou dados históricos. Próxima pesquisa humana: anúncios mobiliados efetivamente disponíveis com datas exatas confirmadas.
