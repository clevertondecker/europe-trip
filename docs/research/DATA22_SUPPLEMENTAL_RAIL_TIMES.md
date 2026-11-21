# DATA22 — Rotas da lista de interesses e destinos suplementares

**Pesquisa revisada:** 21/11/2026  
**Área de impacto:** comparação UX503 de cidades-base e destinos desejados, sem modificar o plano oficial nem os 30×46 registros de pesquisa histórica.

## Objetivo e escopo

A matriz apresentava `Tempo não pesquisado` para Obernai partindo de Metz, Strasbourg, Lille e Mulhouse, além de Lille→Basel. O cadastro de roteiros já permite **Obernai e Lucerna** como destinos suplementares, mas não existiam tempos para eles no comparador de cidades-base. Os valores aqui são mínimos publicados **por direção** para a pesquisa atual, não horários específicos da viagem de 2027.

## 12 referências complementares (novas, em overlay separado)

| Origem | Destino | Mínimo divulgado | Tipo | Fonte | Nota |
|---|---|---:|---|---|---|
| Metz | Obernai | 1h44 (104 min) | Secundária | https://www.thetrainline.com/fr/horaires-train/metz-a-obernai | Ao menos 1 troca |
| Strasbourg | Obernai | 0h28 (28 min) | SNCF | https://www.sncf-connect.com/train/horaires/strasbourg/obernai | Outra página /trajet mostra 0h29 |
| Lille | Obernai | 4h16 (256 min) | SNCF | https://www.sncf-connect.com/train/horaires/lille/obernai | Outras amostras /trajet mostram 4h11–4h13 |
| Mulhouse | Obernai | 1h09 (69 min) | SNCF | https://www.sncf-connect.com/train/horaires/mulhouse/obernai | Página indexada também mostrou 1h22 em outro instante |
| Metz | Lucerna | 3h44 (224 min) | Secundária | https://www.thetrainline.com/train-times/metz-to-lucerne | Ao menos 2 trocas |
| Strasbourg | Lucerna | 2h44 (164 min) | SNCF | https://www.sncf-connect.com/train/trajet/strasbourg/lucerne | Agregador distinto exibe 2h39 |
| Lille | Lucerna | 6h06 (366 min) | Secundária | https://www.thetrainline.com/en/train-times/lille-to-lucerne | Outra amostra indexada mostrava 6h18 |
| Mulhouse | Lucerna | 1h46 (106 min) | SNCF | https://www.sncf-connect.com/train/trajet/mulhouse/lucerne | Referência de mínimo, não duração típica |
| Nancy | Obernai | 2h03 (123 min) | SNCF | https://www.sncf-connect.com/train/horaires/nancy/obernai | Outra página /trajet indicava 2h33 |
| Colmar | Obernai | 0h47 (47 min) | SNCF | https://www.sncf-connect.com/train/horaires/colmar/obernai | Referência de ida |
| Sélestat | Obernai | 0h31 (31 min) | SNCF | https://www.sncf-connect.com/train/horaires/selestat/obernai | TER direto presente na amostra |
| Colmar | Lucerna | 2h06 (126 min) | Secundária | https://www.thetrainline.com/train-times/colmar-to-lucerne | Mínimo do agregador |

**13ª observação — base histórica existente:** Lille→Basel, **4h56 (296 min)**, fonte oficial [SNCF Connect](https://www.sncf-connect.com/train/trajet/lille/bale). Inserida com registro casado no DATA13 + manifesto, sem ampliar nem alterar o conjunto de destinos.

### Política de qualidade

1. O novo `data/data22_supplemental_rail_2026_11.json` admite só destinos suplementares validados e cidades-base existentes na pesquisa de 30 bases. Basel não é uma das 30 bases e portanto não recebe registro nesse overlay.
2. O validador exige URL por direção com origem/destino correspondentes, fonte de domínio aprovado, duração positiva, tipo de fonte e confiança coerentes, notas e data de pesquisa de 2026.
3. A apresentação em `rail_reference_projection_model` é **último recurso**. Uma referência histórica, ROUTES7 ou DATA9–13 anterior sempre tem prioridade. Não altera a fonte canônica nem conta a cobertura suplementar como cobertura dos 30×46 pares.
4. Não se presume rota inversa, serviços diretos, retorno no fim de semana, estação exata, transporte urbano, ingressos, preços ou horários de 2027.
5. Valores de páginas com snapshots divergentes ficam registrados separadamente em `notes`; não se tira uma média nem se calcula tempo por soma de outros trechos.
6. A comparação é somente leitura. Escolhas, preferência e cidade-base oficial continuam sem mutação.

### Validação planejada

- `python -m unittest tests.test_data22_supplemental_rail tests.test_data13_directed_rail_coverage tests.test_routes7_comparison_projection`
- `python -m unittest discover -s tests`
- `python tools/audit_data13_coverage.py --json` (a mudança dos pares canônicos deve ser no máximo uma e não se presume cobertura sem auditoria)
- Reproduzir UX503 para as quatro bases Metz, Strasbourg, Lille, Mulhouse com Obernai, Basel e Lucerna, bem como Nancy, Colmar e Sélestat com os destinos suplementares.
