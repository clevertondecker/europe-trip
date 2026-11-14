# Auditoria da experiência financeira — estilos de vida e orçamento da Europa 2027
Data: 2026-11-14. Fonte principal: `Europa_2027_Base_COMPLETA.md` e planilha `Europa_2027_COMPLETO_ORGANIZADO.xlsm` no Drive. Cenários são históricos e ainda não foram cotados para setembro–novembro/2027.

## Resposta executiva
- R$60 mil / ~65 dias / 2 adultos: **muito apertado** no planejamento original; quase nenhuma margem livre. Maior compromisso de lazer/bares/restaurantes na França limitado a R$2.895.
- R$70 mil / ~70 dias / 2 adultos: **apertado**; a verba de lazer em restaurantes sobe para R$4.954, mas a margem adicional ao fundo de emergência continua só ~R$317. É mais confortável que 60k, não "folgado".
- Reserva de emergência (R$4k / R$5k) já está incluída nos totais históricos; não é saldo disponível para restaurantes.
- Voos multidestinos e imóveis mobiliados para ~60 noites não possuem cotações finais. **Não declarar viabilidade financeira confirmada**.

## Composição histórica da viagem completa (casal; BRL)
| Item | Cenário 60k | Cenário 70k | Natureza |
|---|---:|---:|---|
| Voos e transportes aéreos do casal | 16.620 | 16.920 | Hipótese, sem bilhete |
| Itália ~10 dias | 12.545 | 14.636 | Estimativa |
| França | 23.659 | 29.427 | Estimativa, despesas abaixo |
| Instalação | 1.200 | 1.500 | Estimativa |
| Seguro/taxas | 1.950 | 2.200 | Estimativa |
| Reserva emergência (dentro do total) | 4.000 | 5.000 | Reserva comprometida |
| TOTAL exibido | ~59.975 | 69.683 | R$60k tem diferença ~R$1 nos agregados exibidos |
| Margem até teto | ~25 | ~317 | Folga minúscula |

## Detalhe França — despesas para o casal
| Categoria | 60k: 55 dias | R$/semana | 70k: 60 dias | R$/semana |
|---|---:|---:|---:|---:|
| Moradia | 9.650 | 1.228,18 | 10.937 | 1.276,00 |
| Supermercado | 7.785 | 990,82 | 8.878 | 1.035,77 |
| Bares/restaurantes | 2.895 | 368,45 | 4.954 | 577,97 |
| Transporte local | 1.029 | 130,96 | 1.158 | 135,10 |
| Passeios/ingressos | 2.300 | 292,73 | 3.500 | 408,33 |
| Subtotal | 23.659 | 3.011,15 | 29.427 | 3.433,15 |

Tempos aqui são uma **aproximação operacional**: 65/70 dias de viagem completa menos 10 dias da Itália = 55/60 dias na França. Os valores não são efetivos de compra.

## Saídas e restaurantes
Modelo de sensibilidade transparente: nº de saídas na semana × semanas na França × gasto médio POR CASAL em EUR × câmbio selecionado. A verba já alocada para restaurantes é SUBSTITUÍDA por essa projeção, jamais somada outra vez. Saídas incluem bares, cafés ou restaurantes conforme gasto médio informado. Os preços abaixo são escolhas hipotéticas para entender frequência, não uma cesta de restaurantes cotada.

Simulação para €60 por saída casal e R$6,30/€:
| Saídas/semana | 60k / 55 dias | 70k / 60 dias |
|---|---:|---:|
| 0 | 0 | 0 |
| 1 | 2.970 | 3.240 |
| 2 | 5.940 | 6.480 |
| 3 | 8.910 | 9.720 |
| 4 | 11.880 | 12.960 |

Reforço: o orçamento histórico prevê R$2.895 / R$4.954 para bares/restaurantes; não substitui a verba de passeios pagos R$2.300/R$3.500. No modelo €60 por saída, o limite aproximado puramente de verba de lazer é 0,97 saída/semana (60k) e 1,53 saída/semana (70k) — **e mesmo o próprio orçamento inicial já quase atinge o teto**.

A base de conhecimento antiga possui um estudo independente que estima R$4.963 para 1,5 saídas/semana, R$14.062 para 3 e R$28.540 para 4,5 por 60 dias. Não são somados ao orçamento; métodos e padrão de consumo diferem do simulador por saída. O conjunto alerta que quanto mais frequente e caro o lazer, maior a extrapolação.

Referência externa comum (coleta 2026, colaborativa, não cotação):
- Mulhouse: jantar intermediário 3 pratos para duas pessoas €67,50, https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Mulhouse
- Strasbourg €62,50, https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Strasbourg
- Metz €60, https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Metz-France
- Nancy €60, https://fr.numbeo.com/co%C3%BBt-de-la-vie/ville/Nancy

## Critérios de viabilidade usados na interface
- Saldo negativo: extrapolação do teto e necessidade de reduzir outras rubricas.
- Saldo ≥0 mas inferior a 5% do teto: "apertado", mesmo além da reserva já alocada.
- Saldo ≥5%: "alguma margem" condicional, não atestado financeiro; 5% é heurística de prudência definida para a UI, não regra de mercado.
- A reserva original (4/5k) é destinada a emergência; NÃO equivale a poder de compra para sair mais.
- O simulador de aluguel antigo é independente e **não acumula automaticamente** com este; usuário deve escolher um cenário de cada vez para evitar falsa precisão.

## Como melhorar a confiança do orçamento futuramente
1. Cotar passagens em datas reais Itália/França com bagagens e deslocamentos porta a porta.
2. Obter ao menos três ofertas por cidade para o período exato, duas pessoas, custos totais (incluindo contas, limpeza, taxas, eventual caução reembolsável separada), internet e contrato.
3. Montar orçamento semanal do casal por cidade em supermercados reais e ao menos dois perfis de saídas, usando cardápios locais. Não somar a cesta histórica (€137,06 por semana para dois) novamente, pois a planilha já tem verba de supermercado.
4. Separar passeios locais gratuitos, pagos e excursões interurbanas com custos de dois adultos, entradas e transporte.
5. Fazer reconciliação única dos dois simuladores (aluguel e bares) somente quando necessário, preservando fontes e as despesas já contidas na planilha.
6. Revalidar câmbio, preços em 2027, regras de trabalho remoto e despesas de seguro.

## Implementação
- Prompt: `PROMPT_AUDITORIA_ESTILO_DE_VIDA.md`
- Motor puro: `finance_lifestyle.py`
- Testes: `tests/test_finance_lifestyle.py`
- UI: `app.py` → Orçamento, seções "Dá para viajar com esse valor?", "França: detalhamento das verbas incluídas", "Quantas vezes podemos sair?"
- Dados do Drive NÃO alterados. A análise usa subrubricas históricas e o total global sincronizado; se as subrubricas mudarem no Excel, precisam de nova auditoria e sincronização específica.
