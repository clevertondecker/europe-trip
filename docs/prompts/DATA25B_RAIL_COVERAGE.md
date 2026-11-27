# DATA25B — Ampliação ferroviária com evidência oficial

## Escopo
Onze lacunas DATA24: Angers e Rennes para Lille, Metz, Mulhouse, Nancy e Strasbourg; Metz → Sélestat. Escolhidos por cobertura comum e conexão regional, sem supor que sejam desejos privados. Preservar Annecy e demais registros.

## Evidências
Consulta em 25/11/2026, páginas oficiais SNCF Connect (conteúdo indexado, não busca de serviço ao vivo). Campo mínimo de ida, não média. Sem inferência de retorno, 2027, estação específica, preço ou última milha.

| Origem | Destino | Mínimo | Fonte |
|---|---|---:|---|
| lille | angers | 3h17 | [SNCF](https://www.sncf-connect.com/train/trajet/lille/angers) |
| metz | angers | 4h05 | [SNCF](https://www.sncf-connect.com/train/trajet/metz/angers) |
| mulhouse | angers | 4h54 | [SNCF](https://www.sncf-connect.com/train/trajet/mulhouse/angers) |
| nancy | angers | 3h58 | [SNCF](https://www.sncf-connect.com/train/trajet/nancy/angers) |
| strasbourg | angers | 4h17 | [SNCF](https://www.sncf-connect.com/train/trajet/strasbourg/angers) |
| lille | rennes | 3h25 | [SNCF](https://www.sncf-connect.com/train/trajet/lille/rennes) |
| metz | rennes | 4h11 | [SNCF](https://www.sncf-connect.com/train/trajet/metz/rennes) |
| mulhouse | rennes | 5h10 | [SNCF](https://www.sncf-connect.com/train/trajet/mulhouse/rennes) |
| nancy | rennes | 4h03 | [SNCF](https://www.sncf-connect.com/train/trajet/nancy/rennes) |
| strasbourg | rennes | 4h03 | [SNCF](https://www.sncf-connect.com/train/trajet/strasbourg/rennes) |
| metz | selestat | 1h23 | [SNCF](https://www.sncf-connect.com/train/trajet/metz/selestat) |

Não incorporadas por falta de confirmação nas páginas consultadas: Metz→Fribourg, Metz/Nancy→Interlaken, Nancy→Lucerne, Metz/Nancy/Strasbourg→Trier e Metz/Nancy→Offenburg. Falha de acesso não implica inexistência de trem. Manter lacunas.

## Aceite
Apenas 11 pares passam de sem tempo a indicativo; nenhum outro par modificado. Reusar validador, projeção e fonte por par; manter D-004 aberta, sem alteração de orçamento, TripPlan, wishlist ou UI. Auditoria atualizada e verificação de consistência pela CI. Sem merge sem autorização.
