# DATA 11 — Cobertura dirigida para análise de cidades-base (18/11/2026)

## Objetivo
Viabilizar a comparação exploratória de transportes com dados de ida suficientes
para a tela DQ3.2, sem criar retornos, tarifas ou horários de 2027 fictícios.

## Implementado
- 42 referências **novas no dataset DATA11**: 30 para Mulhouse, cinco para Strasbourg, três para Metz, duas para Nancy, uma para Lille e uma para Colmar.
- Mantida a precedência existente: histórico → ROUTES7 → DATA9 → DATA10 → **DATA11** → desconhecido.
- Dados com direção, mínimo publicado, fonte HTTPS, data da consulta, nível de confiança e limites 2027.
- `decorate_comparison` é a única projeção de transporte, usada pela DQ3.2 e comparadores.
- `opportunity_overview` carrega a proveniência DATA11. Não existem caminhos paralelos para calcular tempos.
- Testes cobrem a exibição de Mulhouse → Arlon, Esch-sur-Alzette, Kehl, Lausanne, Lauterbrunnen, Liège, Lörrach, Metz e Namur e garantem que nem o TripPlan nem o retorno são alterados.

## Evidências pesquisadas (exemplos)
| Origem → destino | Mínimo de ida | Fonte |
|---|---:|---|
| Mulhouse → Metz | 1h50 | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/metz) |
| Mulhouse → Nancy | 2h05 | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/nancy) |
| Mulhouse → Kehl | 1h16 | [Trainline](https://www.thetrainline.com/train-times/mulhouse-to-kehl) |
| Mulhouse → Colmar | 19 min | [SNCF Connect](https://www.sncf-connect.com/train/trajet/mulhouse/colmar) |
| Mulhouse → Strasbourg | 49 min | [SNCF Connect](https://www.sncf-connect.com/train/horaires/mulhouse/strasbourg) |
| Mulhouse → Lauterbrunnen | 2h53 | [Trainline](https://www.thetrainline.com/en/train-times/mulhouse-to-lauterbrunnen) |
| Mulhouse → Interlaken Ost | 2h14 | [Trainline](https://www.thetrainline.com/train-times/mulhouse-to-interlaken-ost) |
| Mulhouse → Arlon | 3h17 | [Trainline](https://www.thetrainline.com/fr/horaires-train/mulhouse-a-arlon) |
| Mulhouse → Esch-sur-Alzette | 3h05 | [Trainline](https://www.thetrainline.com/fr/horaires-train/mulhouse-a-esch-sur-alzette) |
| Mulhouse → Liège | 5h49 | [Trainline](https://www.thetrainline.com/en/train-times/mulhouse-to-liege) |

## Interpretação para o front
A célula de referência inclui texto `~<duração> · mínimo publicado · operadora`
ou `~<duração> · referência secundária · mínimo divulgado`, conforme
a fonte, enquanto uma rota sem referência continua explicitamente desconhecida.
A tela não deve usar duração mínima como tempo típico nem inferir bate-volta.

A DQ3.2 mostra 46 destinos no universo; a cidade-base é um dos locais e
acesso local é tratado separadamente. É incorreto exigir 46 rotas ferroviárias.

## Limites que permanecem
- DATA11 **não cobre 1.380 pares**; além das seis bases priorizadas, todas as
  demais mantêm o nível anterior de pesquisa.
- Alguns novos registros podem já estar cobertos por evidências de precedência
  superior, então 42 registros não implicam 42 células novas no front.
- Os mínimos são sujeitos a variação por dia, operador e estação. Não há
  tarifa definitiva, transferências verificadas, duração típica nem ida e volta
  em setembro–novembro/2027.
- Para Oeschinensee é necessário verificar o acesso via Kandersteg e conexão
  local; não imputar um tempo porta a porta.
- A CI valida integração de dados, mas não substitui inspeção visual do deploy.

## Como reproduzir a cobertura
```bash
python tools/validate_research_data.py
python -m unittest tests.test_data11_priority_connectivity -v
python -m unittest discover -s tests -v
```
