# DATA 12 — Lille, referências ferroviárias adicionais (18/11/2026)

## Diagnóstico
Na captura anterior, Lille mostrava 15 dos 46 destinos com mínimo ou referência.
Faltavam trajetos como Strasbourg, Reims, Saverne, Colmar, Thionville e Metz.

## Alteração
- 26 observações Lille → destino de menor tempo de ida divulgado.
- Fontes: SNCF Connect (19) e Trainline (7).
- Validação idêntica ao DATA10: pares canônicos, URLs autorizadas, confiança
  coerente com fonte, somente ida, nenhum horário de retorno comprovado.
- Sobreposição como fallback estritamente depois de histórico, ROUTES7,
  DATA9, DATA10 e DATA11; não alterar dados mais fortes.
- DQ3.2 e UX503 usam o mesmo resolvedor `decorate_comparison`.
- Registro de fonte, data, confiança e escopo 2026; nada de 2027 garantido.

## Exemplos
| Rota | Duração mínima de ida | Fonte |
|---|---:|---|
| Lille → Reims | 1h50 | https://www.sncf-connect.com/train/trajet/lille/reims |
| Lille → Nancy | 2h47 | https://www.sncf-connect.com/train/trajet/lille/nancy |
| Lille → Metz | 2h59 | https://www.sncf-connect.com/train/horaires/lille/metz |
| Lille → Strasbourg | 3h03 | https://www.sncf-connect.com/train/trajet/lille/strasbourg |
| Lille → Colmar | 3h43 | https://www.sncf-connect.com/train/trajet/lille/colmar |
| Lille → Saverne | 3h42 | https://www.sncf-connect.com/train/trajet/lille/saverne |
| Lille → Kehl | 3h51 | https://www.sncf-connect.com/train/trajet/lille/kehl |
| Lille → Rotterdam | 2h01 | https://www.sncf-connect.com/train/trajet/lille/rotterdam |
| Lille → Ghent | 1h08 | https://www.thetrainline.com/train-times/lille-to-ghent |
| Lille → Arlon | 3h30 | https://www.thetrainline.com/en/train-times/lille-to-arlon |
| Lille → Offenburg | 4h10 | https://www.thetrainline.com/en/train-times/lille-to-offenburg |
| Lille → Freiburg (Breisgau) Hbf | 4h55 | https://www.thetrainline.com/en/train-times/lille-to-freiburg-breisgau-hbf |

**Atenção:** algumas páginas variam segundo data consultada, estação ou
horário; o valor é apenas um mínimo divulgado para triagem. Nunca somar
metade de um retorno imaginário para classificar passeios.

## Regras
- Valor ausente continua ausente, não equivale a local inacessível.
- O trajeto inverso requer fonte independente.
- Retorno, conexão, tarifa do casal e última milha seguem não verificados.
- Não inferir `feasible` de uma duração curta.
- Teste cobre a passagem dataset → projeção → DQ3.2.

## Validação
```bash
python tools/validate_research_data.py
python -m unittest tests.test_data12_lille_connectivity -v
python -m unittest discover -s tests -v
```
Dados adicionais para outras 29 bases permanecem backlog.
